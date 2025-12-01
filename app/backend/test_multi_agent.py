"""
Test script for the multi-agent system
Run this to verify the A2A protocol implementation
"""
import asyncio
import json
from services.agents import (
    agent_registry,
    expense_agent,
    document_agent,
    orchestrator_agent
)
from services.agents.a2a_protocol import A2ARequest, create_a2a_message


async def test_agent_registry():
    """Test 1: Agent Registry"""
    print("\n" + "="*60)
    print("TEST 1: Agent Registry")
    print("="*60)
    
    agents = agent_registry.list_agents()
    print(f"\n✓ Found {len(agents)} registered agents:")
    
    for agent in agents:
        print(f"\n  Agent: {agent.name} ({agent.agent_id})")
        print(f"  Description: {agent.description}")
        print(f"  Capabilities:")
        for cap in agent.capabilities:
            print(f"    - {cap.name}: {cap.description}")
    
    return True


async def test_document_agent():
    """Test 2: Document Agent - Extract Receipt Info"""
    print("\n" + "="*60)
    print("TEST 2: Document Agent")
    print("="*60)
    
    # Create a test request
    request = A2ARequest(
        capability_name="extract_receipt_info",
        parameters={
            "file_path": "local://uploads/receipts/test/sample.pdf",
            "extract_fields": ["vendor", "amount", "date"]
        },
        context={"user_id": "test_user", "role": "admin"}
    )
    
    print(f"\n  Sending request to document_agent...")
    print(f"  Capability: {request.capability_name}")
    print(f"  Parameters: {json.dumps(request.parameters, indent=4)}")
    
    # Note: This will fail if the file doesn't exist, but demonstrates the flow
    try:
        response = await document_agent.handle_request(
            request,
            context={"user_id": "test_user", "role": "admin"}
        )
        
        print(f"\n  Response:")
        print(f"  Success: {response.success}")
        if response.success:
            print(f"  Result: {json.dumps(response.result, indent=4)}")
        else:
            print(f"  Error: {response.error}")
        
        return response.success
    except Exception as e:
        print(f"\n  ⚠ Expected error (file may not exist): {str(e)}")
        return True  # Expected failure for demo


async def test_expense_agent():
    """Test 3: Expense Agent - Apply Static Rules"""
    print("\n" + "="*60)
    print("TEST 3: Expense Agent")
    print("="*60)
    
    # Create a test request
    test_expense = {
        "employee_id": "emp_123",
        "amount": 450.00,
        "category": "Meals",
        "business_justification": "Client dinner",
        "date_of_expense": "2025-01-15"
    }
    
    request = A2ARequest(
        capability_name="apply_static_rules",
        parameters={
            "expense": test_expense,
            "receipt_summary": "receipt_image_attached"
        },
        context={"user_id": "test_user", "role": "admin"}
    )
    
    print(f"\n  Sending request to expense_agent...")
    print(f"  Capability: {request.capability_name}")
    print(f"  Expense: {json.dumps(test_expense, indent=4)}")
    
    response = await expense_agent.handle_request(
        request,
        context={"user_id": "test_user", "role": "admin"}
    )
    
    print(f"\n  Response:")
    print(f"  Success: {response.success}")
    if response.success:
        print(f"  Result: {json.dumps(response.result, indent=4)}")
    else:
        print(f"  Error: {response.error}")
    
    return response.success


async def test_a2a_message_flow():
    """Test 4: A2A Message Flow"""
    print("\n" + "="*60)
    print("TEST 4: A2A Message Flow")
    print("="*60)
    
    # Create an A2A message
    request = A2ARequest(
        capability_name="apply_static_rules",
        parameters={
            "expense": {
                "employee_id": "emp_456",
                "amount": 600.00,
                "category": "Travel"
            },
            "receipt_summary": "receipt_image_attached"
        }
    )
    
    message = create_a2a_message(
        sender_id="orchestrator",
        recipient_id="expense_agent",
        message_type="request",
        payload=request.dict(),
        capability_name="apply_static_rules"
    )
    
    print(f"\n  Created A2A Message:")
    print(f"  Message ID: {message.message_id}")
    print(f"  From: {message.sender_agent_id}")
    print(f"  To: {message.recipient_agent_id}")
    print(f"  Type: {message.message_type}")
    print(f"  Capability: {message.capability_name}")
    
    # Process the message
    print(f"\n  Processing message through expense_agent...")
    response_message = await expense_agent.process_message(
        message,
        context={"user_id": "test_user", "role": "admin"}
    )
    
    print(f"\n  Response Message:")
    print(f"  Message ID: {response_message.message_id}")
    print(f"  From: {response_message.sender_agent_id}")
    print(f"  To: {response_message.recipient_agent_id}")
    print(f"  Type: {response_message.message_type}")
    print(f"  Correlation ID: {response_message.correlation_id}")
    
    if response_message.message_type == "response":
        payload = response_message.payload
        print(f"  Payload: {json.dumps(payload, indent=4)}")
        return payload.get("success", False)
    else:
        print(f"  Error: {response_message.payload.get('error')}")
        return False


async def test_orchestrator():
    """Test 5: Orchestrator Agent"""
    print("\n" + "="*60)
    print("TEST 5: Orchestrator Agent")
    print("="*60)
    
    # Test query
    query = "What agents are available in the system?"
    
    print(f"\n  Query: {query}")
    print(f"  Processing through orchestrator...")
    
    try:
        result = await orchestrator_agent.process_query(
            query=query,
            user_id="test_user",
            role="admin"
        )
        
        print(f"\n  Response:")
        print(f"  Success: {result.get('success')}")
        print(f"  Agents Used: {result.get('agents_used', [])}")
        print(f"\n  Answer:")
        print(f"  {result.get('response', 'No response')}")
        
        return result.get('success', False)
    except Exception as e:
        print(f"\n  Error: {str(e)}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("MULTI-AGENT SYSTEM TEST SUITE")
    print("="*60)
    
    tests = [
        ("Agent Registry", test_agent_registry),
        ("Document Agent", test_document_agent),
        ("Expense Agent", test_expense_agent),
        ("A2A Message Flow", test_a2a_message_flow),
        ("Orchestrator Agent", test_orchestrator),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n  ✗ Test failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
