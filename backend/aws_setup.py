# aws_setup.py
import boto3
import json
import time
from botocore.exceptions import ClientError

class BedrockKnowledgeBaseSetup:
    def __init__(self, region='us-east-1'):
        self.region = region
        self.bedrock = boto3.client('bedrock', region_name=region)
        self.bedrock_agent = boto3.client('bedrock-agent', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.iam = boto3.client('iam', region_name=region)
        self.opensearch = boto3.client('opensearchserverless', region_name=region)
        
    def create_s3_bucket(self, bucket_name):
        """Create S3 bucket for document storage"""
        try:
            if self.region == 'us-east-1':
                self.s3.create_bucket(Bucket=bucket_name)
            else:
                self.s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            print(f"Created S3 bucket: {bucket_name}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                print(f"Bucket {bucket_name} already exists")
                return True
            else:
                print(f"Error creating bucket: {e}")
                return False
    
    def create_iam_role_for_bedrock(self, role_name='BedrockKnowledgeBaseRole'):
        """Create IAM role for Bedrock Knowledge Base"""
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "bedrock.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            role = self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='Role for Bedrock Knowledge Base'
            )
            
            # Attach necessary policies
            policies = [
                'arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess',
                'arn:aws:iam::aws:policy/AmazonBedrockFullAccess'
            ]
            
            for policy in policies:
                self.iam.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy
                )
            
            # Custom policy for OpenSearch Serverless
            opensearch_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "aoss:*"
                        ],
                        "Resource": "*"
                    }
                ]
            }
            
            self.iam.put_role_policy(
                RoleName=role_name,
                PolicyName='OpenSearchServerlessAccess',
                PolicyDocument=json.dumps(opensearch_policy)
            )
            
            print(f"Created IAM role: {role_name}")
            return role['Role']['Arn']
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                role = self.iam.get_role(RoleName=role_name)
                print(f"IAM role {role_name} already exists")
                return role['Role']['Arn']
            else:
                print(f"Error creating IAM role: {e}")
                return None
    
    def create_opensearch_collection(self, collection_name='bedrock-kb-collection'):
        """Create OpenSearch Serverless collection"""
        try:
            # Create security policy
            encryption_policy = {
                "Rules": [
                    {
                        "ResourceType": "collection",
                        "Resource": [f"collection/{collection_name}"]
                    }
                ],
                "AWSOwnedKey": True
            }
            
            self.opensearch.create_security_policy(
                name=f"{collection_name}-encryption",
                type='encryption',
                policy=json.dumps(encryption_policy)
            )
            
            # Create network policy
            network_policy = [
                {
                    "Rules": [
                        {
                            "ResourceType": "collection",
                            "Resource": [f"collection/{collection_name}"]
                        },
                        {
                            "ResourceType": "dashboard",
                            "Resource": [f"collection/{collection_name}"]
                        }
                    ],
                    "AllowFromPublic": True
                }
            ]
            
            self.opensearch.create_security_policy(
                name=f"{collection_name}-network",
                type='network',
                policy=json.dumps(network_policy)
            )
            
            # Create collection
            collection = self.opensearch.create_collection(
                name=collection_name,
                type='VECTORSEARCH',
                description='Collection for Bedrock Knowledge Base'
            )
            
            print(f"Created OpenSearch collection: {collection_name}")
            
            # Wait for collection to be active
            while True:
                response = self.opensearch.list_collections(
                    collectionFilters={'name': collection_name}
                )
                if response['collectionSummaries'][0]['status'] == 'ACTIVE':
                    break
                print("Waiting for collection to be active...")
                time.sleep(30)
            
            return collection['createCollectionDetail']['arn']
            
        except ClientError as e:
            print(f"Error creating OpenSearch collection: {e}")
            return None
    
    def create_knowledge_base(self, kb_name, s3_bucket, role_arn, collection_arn):
        """Create Bedrock Knowledge Base"""
        try:
            kb_config = {
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': f'arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0'
                }
            }
            
            storage_config = {
                'type': 'OPENSEARCH_SERVERLESS',
                'opensearchServerlessConfiguration': {
                    'collectionArn': collection_arn,
                    'vectorIndexName': 'bedrock-knowledge-base-index',
                    'fieldMapping': {
                        'vectorField': 'bedrock-knowledge-base-default-vector',
                        'textField': 'AMAZON_BEDROCK_TEXT_CHUNK',
                        'metadataField': 'AMAZON_BEDROCK_METADATA'
                    }
                }
            }
            
            response = self.bedrock_agent.create_knowledge_base(
                name=kb_name,
                description='Knowledge base for AI Agent',
                roleArn=role_arn,
                knowledgeBaseConfiguration=kb_config,
                storageConfiguration=storage_config
            )
            
            kb_id = response['knowledgeBase']['knowledgeBaseId']
            print(f"Created Knowledge Base: {kb_name} (ID: {kb_id})")
            
            # Create data source
            data_source_config = {
                'type': 'S3',
                's3Configuration': {
                    'bucketArn': f'arn:aws:s3:::{s3_bucket}',
                    'inclusionPrefixes': ['documents/']
                }
            }
            
            chunking_config = {
                'chunkingStrategy': 'FIXED_SIZE',
                'fixedSizeChunkingConfiguration': {
                    'maxTokens': 500,
                    'overlapPercentage': 20
                }
            }
            
            data_source = self.bedrock_agent.create_data_source(
                knowledgeBaseId=kb_id,
                name=f"{kb_name}-s3-datasource",
                description='S3 data source for knowledge base',
                dataSourceConfiguration=data_source_config,
                vectorIngestionConfiguration={
                    'chunkingConfiguration': chunking_config
                }
            )
            
            print(f"Created data source: {data_source['dataSource']['dataSourceId']}")
            
            return kb_id, data_source['dataSource']['dataSourceId']
            
        except ClientError as e:
            print(f"Error creating knowledge base: {e}")
            return None, None
    
    def upload_sample_documents(self, bucket_name):
        """Upload sample documents to S3"""
        sample_docs = [
            {
                'filename': 'ai_basics.txt',
                'content': """
                Artificial Intelligence (AI) Overview
                
                Artificial Intelligence is the simulation of human intelligence in machines that are programmed to think and learn like humans. The term may also be applied to any machine that exhibits traits associated with a human mind such as learning and problem-solving.
                
                Types of AI:
                1. Narrow AI (Weak AI): AI that is designed and trained for a particular task
                2. General AI (Strong AI): AI with generalized human cognitive abilities
                3. Superintelligence: AI that surpasses human intelligence
                
                Applications of AI:
                - Natural Language Processing
                - Computer Vision
                - Machine Learning
                - Robotics
                - Expert Systems
                
                Key Technologies:
                - Neural Networks
                - Deep Learning
                - Reinforcement Learning
                - Natural Language Understanding
                """
            },
            {
                'filename': 'machine_learning.txt',
                'content': """
                Machine Learning Fundamentals
                
                Machine Learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention.
                
                Types of Machine Learning:
                1. Supervised Learning: Learning with labeled data
                   - Classification
                   - Regression
                
                2. Unsupervised Learning: Learning from data without labels
                   - Clustering
                   - Association
                
                3. Reinforcement Learning: Learning through interaction with environment
                   - Reward-based learning
                   - Policy optimization
                
                Common Algorithms:
                - Linear Regression
                - Decision Trees
                - Random Forest
                - Support Vector Machines
                - Neural Networks
                - K-Means Clustering
                
                Applications:
                - Image Recognition
                - Speech Recognition
                - Recommendation Systems
                - Fraud Detection
                - Autonomous Vehicles
                """
            },
            {
                'filename': 'aws_bedrock.txt',
                'content': """
                AWS Bedrock Overview
                
                Amazon Bedrock is a fully managed service that offers a choice of high-performing foundation models (FMs) from leading AI companies like AI21 Labs, Anthropic, Cohere, Meta, Stability AI, and Amazon via a single API.
                
                Key Features:
                1. Choice of Foundation Models
                2. Easy Model Customization
                3. Serverless Experience
                4. Security and Privacy
                5. Responsible AI
                
                Foundation Models Available:
                - Amazon Titan (Text and Embeddings)
                - Anthropic Claude
                - AI21 Labs Jurassic
                - Cohere Command
                - Meta Llama
                - Stability AI Stable Diffusion
                
                Use Cases:
                - Text Generation
                - Chatbots and Virtual Assistants
                - Text Summarization
                - Image Generation
                - Code Generation
                - Search and Discovery
                
                Bedrock Features:
                - Knowledge Bases for RAG
                - Agents for complex workflows
                - Model Evaluation
                - Guardrails for responsible AI
                - Fine-tuning capabilities
                """
            }
        ]
        
        for doc in sample_docs:
            try:
                self.s3.put_object(
                    Bucket=bucket_name,
                    Key=f"documents/{doc['filename']}",
                    Body=doc['content'].encode('utf-8'),
                    ContentType='text/plain'
                )
                print(f"Uploaded: {doc['filename']}")
            except ClientError as e:
                print(f"Error uploading {doc['filename']}: {e}")
    
    def sync_knowledge_base(self, kb_id, data_source_id):
        """Sync the knowledge base to ingest documents"""
        try:
            response = self.bedrock_agent.start_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=data_source_id,
                description='Initial document ingestion'
            )
            
            job_id = response['ingestionJob']['ingestionJobId']
            print(f"Started ingestion job: {job_id}")
            
            # Wait for ingestion to complete
            while True:
                status = self.bedrock_agent.get_ingestion_job(
                    knowledgeBaseId=kb_id,
                    dataSourceId=data_source_id,
                    ingestionJobId=job_id
                )
                
                current_status = status['ingestionJob']['status']
                print(f"Ingestion status: {current_status}")
                
                if current_status in ['COMPLETE', 'FAILED']:
                    break
                
                time.sleep(30)
            
            return current_status == 'COMPLETE'
            
        except ClientError as e:
            print(f"Error syncing knowledge base: {e}")
            return False
    
    def setup_complete_system(self, project_name='ai-agent'):
        """Set up the complete system"""
        print("Starting AWS Bedrock Knowledge Base setup...")
        
        # Generate unique names
        bucket_name = f"{project_name}-documents-{int(time.time())}"
        collection_name = f"{project_name}-kb-collection"
        kb_name = f"{project_name}-knowledge-base"
        role_name = f"{project_name}-bedrock-role"
        
        # Step 1: Create S3 bucket
        if not self.create_s3_bucket(bucket_name):
            return None
        
        # Step 2: Create IAM role
        role_arn = self.create_iam_role_for_bedrock(role_name)
        if not role_arn:
            return None
        
        # Step 3: Create OpenSearch collection
        collection_arn = self.create_opensearch_collection(collection_name)
        if not collection_arn:
            return None
        
        # Step 4: Upload sample documents
        self.upload_sample_documents(bucket_name)
        
        # Step 5: Create knowledge base
        kb_id, data_source_id = self.create_knowledge_base(
            kb_name, bucket_name, role_arn, collection_arn
        )
        
        if not kb_id:
            return None
        
        # Step 6: Sync knowledge base
        print("Waiting 60 seconds before starting ingestion...")
        time.sleep(60)
        
        success = self.sync_knowledge_base(kb_id, data_source_id)
        
        if success:
            print("\n✅ Setup completed successfully!")
            print(f"Knowledge Base ID: {kb_id}")
            print(f"S3 Bucket: {bucket_name}")
            print(f"Data Source ID: {data_source_id}")
            
            return {
                'knowledge_base_id': kb_id,
                'data_source_id': data_source_id,
                'bucket_name': bucket_name,
                'collection_name': collection_name,
                'role_arn': role_arn
            }
        else:
            print("❌ Setup failed during document ingestion")
            return None

if __name__ == "__main__":
    # Initialize setup
    setup = BedrockKnowledgeBaseSetup(region='us-east-1')  # Change region as needed
    
    # Run complete setup
    result = setup.setup_complete_system('my-ai-agent')
    
    if result:
        # Save configuration for later use
        with open('bedrock_config.json', 'w') as f:
            json.dump(result, f, indent=2)
        
        print("\nConfiguration saved to bedrock_config.json")
        print("You can now update your FastAPI backend with the knowledge_base_id")
    else:
        print("Setup failed. Please check the errors above.")