"""
Test script for the Orchestrator endpoint
Run this after starting the backend server
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
# Replace with your actual Firebase token from the emulator or production
FIREBASE_TOKEN = "your_firebase_token_here"

def test_orchestrator(query: str):
    """Test the orchestrator endpoint with a query"""
    url = f"{BASE_URL}/orchestrator/"
    headers = {
        "Authorization": f"Bearer {FIREBASE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {"query": query}
    
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        print(f"\n✅ Success: {result['success']}")
        print(f"\n📝 Response:\n{result.get('response', 'N/A')}")
        print(f"\n🔧 Tools Used: {', '.join(result.get('tools_used', []))}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return None

def main():
    """Run test queries"""
    
    print("🚀 Orchestrator Test Script")
    print(f"Testing endpoint: {BASE_URL}/orchestrator/")
    print("\nNote: Make sure the backend server is running!")
    print("Update FIREBASE_TOKEN in this script with your actual token.\n")
    
    # Test queries
    test_queries = [
        "List all employees",
        "Show me all expenses",
        "What are the current reimbursement policies?",
        "Get me the audit logs",
        "Show me employee with ID emp123",
        "Create a new employee named Jane Smith with email jane@example.com",
    ]
    
    for query in test_queries:
        test_orchestrator(query)
        input("\nPress Enter to continue to next test...")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()
