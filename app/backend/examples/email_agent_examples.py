"""
Email Agent Usage Examples

This file demonstrates various ways to use the Email Agent in the ExpenseSense system.
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.agents.email_agent_service import email_agent
from services.agents.orchestrator_agent import orchestrator_agent
from services.agents.a2a_protocol import A2ARequest, create_a2a_message


async def example_1_direct_expense_notification():
    """
    Example 1: Send expense notification directly via A2A protocol
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Direct Expense Notification via A2A")
    print("="*70)
    
    # Create the request
    request = A2ARequest(
        capability_name="send_expense_notification",
        parameters={
            "to": "john.doe@company.com",
            "expense_id": "exp_2025_001",
            "status": "approved",
            "amount": 89.99,
            "category": "Meals",
            "decision_reason": "R1: Receipt valid, within policy limits, first request of day"
        },
        context={"user_id": "system", "role": "system"}
    )
    
    # Create A2A message
    message = create_a2a_message(
        sender_id="expense_agent",
        recipient_id="email_agent",
        message_type="request",
        payload=request.model_dump(),
        capability_name="send_expense_notification"
    )
    
    # Send message
    response = await email_agent.process_message(
        message,
        context={"user_id": "system", "role": "system"}
    )
    
    # Check result
    if response.message_type == "response":
        result = response.payload.get("result", {})
        print(f"\n✅ Success!")
        print(f"   Email sent to: {result.get('to')}")
        print(f"   Subject: {result.get('subject')}")
        print(f"   Message ID: {result.get('message_id')}")
    else:
        print(f"\n❌ Error: {response.payload.get('error')}")


async def example_2_generic_email():
    """
    Example 2: Send a generic email
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Send Generic Email")
    print("="*70)
    
    request = A2ARequest(
        capability_name="send_email",
        parameters={
            "to": "manager@company.com",
            "subject": "Weekly Expense Report Summary",
            "body": """Dear Manager,

Here is the weekly expense report summary:

- Total Expenses: $1,234.56
- Approved: 15
- Rejected: 2
- Pending Review: 3

Please review the pending expenses at your earliest convenience.

Best regards,
ExpenseSense System"""
        },
        context={"user_id": "system", "role": "admin"}
    )
    
    message = create_a2a_message(
        sender_id="reporting_system",
        recipient_id="email_agent",
        message_type="request",
        payload=request.model_dump(),
        capability_name="send_email"
    )
    
    response = await email_agent.process_message(
        message,
        context={"user_id": "system", "role": "admin"}
    )
    
    if response.message_type == "response":
        result = response.payload.get("result", {})
        print(f"\n✅ Success!")
        print(f"   Email sent to: {result.get('to')}")
        print(f"   Subject: {result.get('subject')}")
    else:
        print(f"\n❌ Error: {response.payload.get('error')}")


async def example_3_orchestrator_natural_language():
    """
    Example 3: Use orchestrator with natural language
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Orchestrator Natural Language")
    print("="*70)
    
    queries = [
        "Send an email to alice@company.com with subject 'Welcome' and body 'Welcome to ExpenseSense!'",
        "Notify bob@company.com that his expense was approved",
        "Email the team about the new expense policy"
    ]
    
    for query in queries:
        print(f"\n📝 Query: {query}")
        
        result = await orchestrator_agent.process_query(
            query=query,
            user_id="admin_user",
            role="admin"
        )
        
        if result.get("success"):
            print(f"✅ Response: {result.get('response')}")
            if result.get('agents_used'):
                print(f"   Agents used: {', '.join(result.get('agents_used'))}")
        else:
            print(f"❌ Error: {result.get('error')}")


async def example_4_batch_notifications():
    """
    Example 4: Send multiple notifications (batch)
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Batch Expense Notifications")
    print("="*70)
    
    expenses = [
        {
            "to": "employee1@company.com",
            "expense_id": "exp_001",
            "status": "approved",
            "amount": 45.00,
            "category": "Transportation"
        },
        {
            "to": "employee2@company.com",
            "expense_id": "exp_002",
            "status": "rejected",
            "amount": 250.00,
            "category": "Entertainment"
        },
        {
            "to": "employee3@company.com",
            "expense_id": "exp_003",
            "status": "admin_review",
            "amount": 550.00,
            "category": "Travel"
        }
    ]
    
    print(f"\nSending {len(expenses)} notifications...")
    
    tasks = []
    for expense in expenses:
        request = A2ARequest(
            capability_name="send_expense_notification",
            parameters={
                **expense,
                "decision_reason": f"Automated review for {expense['expense_id']}"
            },
            context={"user_id": "system", "role": "system"}
        )
        
        message = create_a2a_message(
            sender_id="batch_processor",
            recipient_id="email_agent",
            message_type="request",
            payload=request.model_dump(),
            capability_name="send_expense_notification"
        )
        
        task = email_agent.process_message(message, context={})
        tasks.append(task)
    
    # Send all emails concurrently
    responses = await asyncio.gather(*tasks)
    
    # Check results
    success_count = sum(1 for r in responses if r.message_type == "response")
    print(f"\n✅ Successfully sent {success_count}/{len(expenses)} notifications")


async def example_5_error_handling():
    """
    Example 5: Error handling
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: Error Handling")
    print("="*70)
    
    # Test with missing required parameters
    print("\n📝 Test 1: Missing required parameter")
    request = A2ARequest(
        capability_name="send_email",
        parameters={
            "to": "test@company.com",
            "subject": "Test"
            # Missing 'body' parameter
        },
        context={"user_id": "test", "role": "admin"}
    )
    
    message = create_a2a_message(
        sender_id="test",
        recipient_id="email_agent",
        message_type="request",
        payload=request.model_dump(),
        capability_name="send_email"
    )
    
    response = await email_agent.process_message(message, context={})
    
    if response.message_type == "error":
        print(f"✅ Error correctly caught: {response.payload.get('error')}")
    else:
        print(f"❌ Should have failed but didn't")
    
    # Test with invalid capability
    print("\n📝 Test 2: Invalid capability")
    request = A2ARequest(
        capability_name="invalid_capability",
        parameters={},
        context={"user_id": "test", "role": "admin"}
    )
    
    message = create_a2a_message(
        sender_id="test",
        recipient_id="email_agent",
        message_type="request",
        payload=request.model_dump(),
        capability_name="invalid_capability"
    )
    
    response = await email_agent.process_message(message, context={})
    
    if response.message_type == "error":
        print(f"✅ Error correctly caught: {response.payload.get('error')}")
    else:
        print(f"❌ Should have failed but didn't")


async def example_6_agent_discovery():
    """
    Example 6: Discover email agent capabilities
    """
    print("\n" + "="*70)
    print("EXAMPLE 6: Agent Discovery")
    print("="*70)
    
    # Get agent card
    card = email_agent.get_agent_card()
    
    print(f"\n📧 Agent: {card.name}")
    print(f"   ID: {card.agent_id}")
    print(f"   Version: {card.version}")
    print(f"   Description: {card.description}")
    
    print(f"\n🔧 Capabilities ({len(card.capabilities)}):")
    for cap in card.capabilities:
        print(f"\n   • {cap.name}")
        print(f"     {cap.description}")
        print(f"     Required params: {cap.input_schema.get('required', [])}")
    
    print(f"\n📊 Metadata:")
    for key, value in card.metadata.items():
        print(f"   {key}: {value}")


async def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("EMAIL AGENT USAGE EXAMPLES")
    print("="*70)
    
    try:
        await example_1_direct_expense_notification()
        await example_2_generic_email()
        await example_3_orchestrator_natural_language()
        await example_4_batch_notifications()
        await example_5_error_handling()
        await example_6_agent_discovery()
        
        print("\n" + "="*70)
        print("ALL EXAMPLES COMPLETED")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Examples failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
