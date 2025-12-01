"""
Examples of using the Multi-Agent System
These examples show how to interact with the agents via API
"""
import requests
import json

# Base URL for the backend
BASE_URL = "http://localhost:8000"

# Test token for emulator mode
TOKEN = "test-token-12345"

# Headers for all requests
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}


def example_1_list_agents():
    """
    Example 1: List all registered agents and their capabilities
    """
    print("\n" + "="*60)
    print("EXAMPLE 1: List All Agents")
    print("="*60)
    
    response = requests.get(
        f"{BASE_URL}/agents/registry",
        headers=HEADERS
    )
    
    data = response.json()
    
    print(f"\nFound {data['count']} agents:")
    for agent in data['agents']:
        print(f"\n  Agent: {agent['name']}")
        print(f"  ID: {agent['agent_id']}")
        print(f"  Description: {agent['description']}")
        print(f"  Capabilities:")
        for cap in agent['capabilities']:
            print(f"    - {cap['name']}: {cap['description']}")


def example_2_get_agent_card():
    """
    Example 2: Get a specific agent's card
    """
    print("\n" + "="*60)
    print("EXAMPLE 2: Get Expense Agent Card")
    print("="*60)
    
    response = requests.get(
        f"{BASE_URL}/agents/registry/expense_agent",
        headers=HEADERS
    )
    
    data = response.json()
    agent = data['agent']
    
    print(f"\nAgent: {agent['name']}")
    print(f"Version: {agent['version']}")
    print(f"\nCapabilities:")
    for cap in agent['capabilities']:
        print(f"\n  {cap['name']}:")
        print(f"  Description: {cap['description']}")
        print(f"  Input Schema: {json.dumps(cap['input_schema'], indent=4)}")
        print(f"  Output Schema: {json.dumps(cap['output_schema'], indent=4)}")


def example_3_simple_query():
    """
    Example 3: Simple query to list available agents
    """
    print("\n" + "="*60)
    print("EXAMPLE 3: Simple Query")
    print("="*60)
    
    query = "What agents are available in the system?"
    
    response = requests.post(
        f"{BASE_URL}/agents/query",
        headers=HEADERS,
        json={"query": query}
    )
    
    data = response.json()
    
    print(f"\nQuery: {query}")
    print(f"\nResponse:")
    print(f"  Success: {data['success']}")
    print(f"  Agents Used: {data['agents_used']}")
    print(f"\n  Answer:")
    print(f"  {data['response']}")


def example_4_review_expense():
    """
    Example 4: Ask orchestrator to review an expense
    """
    print("\n" + "="*60)
    print("EXAMPLE 4: Review Expense")
    print("="*60)
    
    # First, create a test expense (using direct API)
    print("\n  Step 1: Creating test expense...")
    
    expense_data = {
        "employee_id": "emp_test_123",
        "amount": 450.00,
        "category": "Meals",
        "business_justification": "Client dinner meeting",
        "date_of_expense": "2025-01-15"
    }
    
    # Note: This would normally create an expense via /expenses endpoint
    # For this example, we'll assume expense exp_test_123 exists
    
    # Now ask the orchestrator to review it
    print("\n  Step 2: Asking orchestrator to review...")
    
    query = "Review expense exp_test_123"
    
    response = requests.post(
        f"{BASE_URL}/agents/query",
        headers=HEADERS,
        json={"query": query}
    )
    
    data = response.json()
    
    print(f"\nQuery: {query}")
    print(f"\nResponse:")
    print(f"  Success: {data['success']}")
    print(f"  Agents Used: {data['agents_used']}")
    print(f"\n  Answer:")
    print(f"  {data['response']}")


def example_5_extract_receipt():
    """
    Example 5: Extract information from a receipt
    """
    print("\n" + "="*60)
    print("EXAMPLE 5: Extract Receipt Information")
    print("="*60)
    
    # Assume we have a receipt at this path
    file_path = "local://uploads/receipts/test_user/sample_receipt.pdf"
    
    query = f"Extract information from the receipt at {file_path}"
    
    response = requests.post(
        f"{BASE_URL}/agents/query",
        headers=HEADERS,
        json={"query": query}
    )
    
    data = response.json()
    
    print(f"\nQuery: {query}")
    print(f"\nResponse:")
    print(f"  Success: {data['success']}")
    print(f"  Agents Used: {data['agents_used']}")
    print(f"\n  Answer:")
    print(f"  {data['response']}")


def example_6_upload_and_process():
    """
    Example 6: Upload a receipt file and process it
    """
    print("\n" + "="*60)
    print("EXAMPLE 6: Upload and Process Receipt")
    print("="*60)
    
    # This example shows how to upload a file
    # In practice, you'd have an actual PDF file
    
    query = "Extract information from this receipt and tell me what you found"
    
    # For file upload, we use multipart/form-data
    files = {
        'files': ('receipt.pdf', open('sample_receipt.pdf', 'rb'), 'application/pdf')
    }
    
    data = {
        'query': query
    }
    
    headers = {
        "Authorization": f"Bearer {TOKEN}"
        # Note: Don't set Content-Type for multipart/form-data
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/agents/query-with-files",
            headers=headers,
            data=data,
            files=files
        )
        
        result = response.json()
        
        print(f"\nQuery: {query}")
        print(f"\nResponse:")
        print(f"  Success: {result['success']}")
        print(f"  Agents Used: {result['agents_used']}")
        print(f"\n  Answer:")
        print(f"  {result['response']}")
    except FileNotFoundError:
        print("\n  Note: sample_receipt.pdf not found. This is just an example.")
        print("  In practice, you would provide an actual PDF file.")


def example_7_conversation():
    """
    Example 7: Multi-turn conversation with message history
    """
    print("\n" + "="*60)
    print("EXAMPLE 7: Conversation with History")
    print("="*60)
    
    # First message
    query1 = "What can you help me with?"
    
    response1 = requests.post(
        f"{BASE_URL}/agents/query",
        headers=HEADERS,
        json={"query": query1}
    )
    
    data1 = response1.json()
    
    print(f"\nUser: {query1}")
    print(f"Assistant: {data1['response']}")
    
    # Second message with history
    message_history = [
        {"role": "user", "content": query1},
        {"role": "assistant", "content": data1['response']}
    ]
    
    query2 = "Can you review an expense for me?"
    
    response2 = requests.post(
        f"{BASE_URL}/agents/query",
        headers=HEADERS,
        json={
            "query": query2,
            "message_history": message_history
        }
    )
    
    data2 = response2.json()
    
    print(f"\nUser: {query2}")
    print(f"Assistant: {data2['response']}")


def example_8_complex_workflow():
    """
    Example 8: Complex workflow - Upload receipt, extract info, create expense
    """
    print("\n" + "="*60)
    print("EXAMPLE 8: Complex Workflow")
    print("="*60)
    
    query = """
    I have a receipt for a business lunch. Can you:
    1. Extract the information from the receipt
    2. Create an expense with that information
    3. Review the expense
    4. Tell me the final status
    """
    
    # In practice, you'd upload the actual file
    # For this example, we'll just show the query
    
    print(f"\nQuery: {query}")
    print("\nThis would:")
    print("  1. Call document_agent.extract_receipt_info()")
    print("  2. Use extracted data to create expense")
    print("  3. Call expense_agent.review_expense()")
    print("  4. Return comprehensive status")
    
    # Uncomment to actually run:
    # response = requests.post(
    #     f"{BASE_URL}/agents/query-with-files",
    #     headers={"Authorization": f"Bearer {TOKEN}"},
    #     data={"query": query},
    #     files={'files': ('receipt.pdf', open('receipt.pdf', 'rb'), 'application/pdf')}
    # )
    # data = response.json()
    # print(f"\nResponse: {data['response']}")


def main():
    """
    Run all examples
    """
    print("\n" + "="*60)
    print("MULTI-AGENT SYSTEM API EXAMPLES")
    print("="*60)
    print("\nNote: Make sure the backend is running on http://localhost:8000")
    print("      and you're using emulator mode for authentication.")
    
    examples = [
        ("List All Agents", example_1_list_agents),
        ("Get Agent Card", example_2_get_agent_card),
        ("Simple Query", example_3_simple_query),
        ("Review Expense", example_4_review_expense),
        ("Extract Receipt", example_5_extract_receipt),
        ("Upload and Process", example_6_upload_and_process),
        ("Conversation", example_7_conversation),
        ("Complex Workflow", example_8_complex_workflow),
    ]
    
    for name, example_func in examples:
        try:
            example_func()
        except requests.exceptions.ConnectionError:
            print(f"\n  ✗ Error: Could not connect to backend at {BASE_URL}")
            print("    Make sure the backend is running: python app.py")
            break
        except Exception as e:
            print(f"\n  ✗ Error in {name}: {str(e)}")
    
    print("\n" + "="*60)
    print("EXAMPLES COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
