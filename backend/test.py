# test_mcp_integration.py
# Save this in your backend folder and run it to test MCP integration

import requests
import json
import time
from typing import Dict, Any

class MCPIntegrationTester:
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.session = requests.Session()
    
    def test_backend_health(self) -> Dict[str, Any]:
        """Test if FastAPI backend is running"""
        print("🔍 Testing FastAPI Backend Health...")
        try:
            response = self.session.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ FastAPI Backend: HEALTHY")
                return {"status": "healthy", "details": response.json()}
            else:
                print(f"❌ FastAPI Backend: ERROR ({response.status_code})")
                return {"status": "error", "code": response.status_code}
        except requests.exceptions.RequestException as e:
            print(f"❌ FastAPI Backend: CONNECTION FAILED - {e}")
            return {"status": "connection_failed", "error": str(e)}
    
    def test_mcp_connection(self) -> Dict[str, Any]:
        """Test MCP server connection through backend"""
        print("\n🔍 Testing MCP Server Connection...")
        try:
            response = self.session.get(f"{self.backend_url}/test-mcp-connection", timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    print("✅ MCP Server: CONNECTED")
                    print(f"   📦 Available Tools: {data.get('total_tools', 0)}")
                    print(f"   🛠️  Tool Names: {', '.join(data.get('available_tools', []))}")
                    return data
                else:
                    print(f"❌ MCP Server: {data.get('mcp_server_status', 'UNKNOWN ERROR')}")
                    return data
            else:
                print(f"❌ MCP Test Endpoint: HTTP {response.status_code}")
                return {"status": "http_error", "code": response.status_code}
        except requests.exceptions.RequestException as e:
            print(f"❌ MCP Connection Test: FAILED - {e}")
            return {"status": "request_failed", "error": str(e)}
    
    def test_mcp_tool(self, tool_name: str, tool_args: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test a specific MCP tool"""
        print(f"\n🔍 Testing MCP Tool: {tool_name}")
        try:
            payload = {
                "tool_name": tool_name,
                "tool_args": tool_args or {}
            }
            response = self.session.post(
                f"{self.backend_url}/test-mcp-tool", 
                json=payload, 
                timeout=20
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    print(f"✅ Tool '{tool_name}': WORKING")
                    result = data.get("result", {})
                    if isinstance(result, dict) and "content" in result:
                        content = result["content"][0]["text"] if result["content"] else ""
                        print(f"   📝 Sample Output: {content[:100]}...")
                    return data
                else:
                    print(f"❌ Tool '{tool_name}': FAILED - {data.get('error', 'Unknown error')}")
                    return data
            else:
                print(f"❌ Tool Test: HTTP {response.status_code}")
                return {"status": "http_error", "code": response.status_code}
        except requests.exceptions.RequestException as e:
            print(f"❌ Tool Test: FAILED - {e}")
            return {"status": "request_failed", "error": str(e)}
    
    def test_full_integration(self) -> Dict[str, Any]:
        """Test full MCP integration"""
        print(f"\n🔍 Testing Full MCP Integration...")
        try:
            response = self.session.get(f"{self.backend_url}/mcp-status", timeout=20)
            if response.status_code == 200:
                data = response.json()
                overall_status = data.get("overall_status", "unknown")
                integration_working = data.get("integration_working", False)
                
                if overall_status == "healthy" and integration_working:
                    print("✅ Full Integration: WORKING PERFECTLY")
                    print("   🎉 Ready for Claude integration!")
                else:
                    print(f"⚠️  Integration Status: {overall_status.upper()}")
                    recommendations = data.get("recommendations", [])
                    for rec in recommendations:
                        print(f"   💡 {rec}")
                return data
            else:
                print(f"❌ Integration Test: HTTP {response.status_code}")
                return {"status": "http_error", "code": response.status_code}
        except requests.exceptions.RequestException as e:
            print(f"❌ Integration Test: FAILED - {e}")
            return {"status": "request_failed", "error": str(e)}
    
    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 MCP Integration Comprehensive Test")
        print("=" * 50)
        
        # Test 1: Backend Health
        backend_result = self.test_backend_health()
        
        # Test 2: MCP Connection (only if backend is healthy)
        if backend_result.get("status") == "healthy":
            mcp_result = self.test_mcp_connection()
            
            # Test 3: Individual Tools (only if MCP is connected)
            if mcp_result.get("status") == "success":
                # Test key tools
                tools_to_test = [
                    ("list_agent_modes", {}),
                    ("check_system_health", {}),
                    ("chat_with_agent", {"message": "Hello, test message", "agent_mode": "explainer"})
                ]
                
                tool_results = []
                for tool_name, tool_args in tools_to_test:
                    result = self.test_mcp_tool(tool_name, tool_args)
                    tool_results.append(result)
                    time.sleep(1)  # Small delay between tests
                
                # Test 4: Full Integration
                integration_result = self.test_full_integration()
                
                # Summary
                print("\n" + "=" * 50)
                print("📊 TEST SUMMARY")
                print("=" * 50)
                
                working_tools = sum(1 for r in tool_results if r.get("status") == "success")
                total_tools = len(tool_results)
                
                print(f"🖥️  Backend Health: {'✅ HEALTHY' if backend_result.get('status') == 'healthy' else '❌ ISSUES'}")
                print(f"🔗 MCP Connection: {'✅ CONNECTED' if mcp_result.get('status') == 'success' else '❌ FAILED'}")
                print(f"🛠️  Tool Tests: {'✅' if working_tools == total_tools else '⚠️'} {working_tools}/{total_tools} working")
                print(f"🎯 Integration: {'✅ READY' if integration_result.get('integration_working') else '❌ ISSUES'}")
                
                if integration_result.get("integration_working"):
                    print("\n🎉 SUCCESS: Your MCP integration is working perfectly!")
                    print("   You can now use this with Claude in VS Code or Claude Desktop.")
                else:
                    print("\n⚠️  ISSUES DETECTED:")
                    for rec in integration_result.get("recommendations", []):
                        print(f"   💡 {rec}")
            else:
                print("\n❌ Cannot test tools - MCP server not connected")
        else:
            print("\n❌ Cannot test MCP - Backend not healthy")

def main():
    """Main test function"""
    print("Starting MCP Integration Test...")
    print("Make sure your FastAPI backend is running on port 8000")
    print("Make sure your FastMCP server file is in ../fastmcp-server/")
    
    input("\nPress Enter to start testing...")
    
    tester = MCPIntegrationTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()