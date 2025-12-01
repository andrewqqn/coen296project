"""
Test script for Email Agent A2A integration
"""
import asyncio
import logging
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.agents.email_agent_service import email_agent
from services.agents.a2a_protocol import A2ARequest, create_a2a_message

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_send_expense_notification():
    """Test sending an expense notification"""
    print("\n" + "="*60)
    print("TEST 1: Send Expense Notification")
    print("="*60)
    
    request = A2ARequest(
        capability_name="send_expense_notification",
        parameters={
            "to": "employee@example.com",
            "expense_id": "exp_test_123",
            "status": "approved",
            "amount": 125.50,
            "category": "Meals",
            "decision_reason": "R1: Receipt valid, within policy limits"
        },
        context={"user_id": "test_user", "role": "system"}
    )
    
    message = create_a2a_message(
        sender_id="test_orchestrator",
        recipient_id="email_agent",
        message_type="request",
        payload=request.dict(),
        capability_name="send_expense_notification"
    )
    
    response = await email_agent.process_message(message, context={"user_id": "test_user", "role": "system"})
    
    print(f"\nResponse Type: {response.message_type}")
    print(f"Response Payload: {response.payload}")
    
    if response.message_type == "response":
        result = response.payload.get("result", {})
        print(f"\n✅ Email sent successfully!")
        print(f"   To: {result.get('to')}")
        print(f"   Subject: {result.get('subject')}")
        print(f"   Message ID: {result.get('message_id')}")
    else:
        print(f"\n❌ Error: {response.payload.get('error')}")


async def test_send_generic_email():
    """Test sending a generic email"""
    print("\n" + "="*60)
    print("TEST 2: Send Generic Email")
    print("="*60)
    
    request = A2ARequest(
        capability_name="send_email",
        parameters={
            "to": "admin@example.com",
            "subject": "Test Email from Email Agent",
            "body": "This is a test email sent via the A2A protocol.\n\nBest regards,\nEmail Agent"
        },
        context={"user_id": "test_user", "role": "admin"}
    )
    
    message = create_a2a_message(
        sender_id="test_orchestrator",
        recipient_id="email_agent",
        message_type="request",
        payload=request.dict(),
        capability_name="send_email"
    )
    
    response = await email_agent.process_message(message, context={"user_id": "test_user", "role": "admin"})
    
    print(f"\nResponse Type: {response.message_type}")
    print(f"Response Payload: {response.payload}")
    
    if response.message_type == "response":
        result = response.payload.get("result", {})
        print(f"\n✅ Email sent successfully!")
        print(f"   To: {result.get('to')}")
        print(f"   Subject: {result.get('subject')}")
    else:
        print(f"\n❌ Error: {response.payload.get('error')}")


async def test_agent_card():
    """Test getting the agent card"""
    print("\n" + "="*60)
    print("TEST 3: Get Agent Card")
    print("="*60)
    
    card = email_agent.get_agent_card()
    
    print(f"\nAgent ID: {card.agent_id}")
    print(f"Name: {card.name}")
    print(f"Description: {card.description}")
    print(f"Version: {card.version}")
    print(f"\nCapabilities:")
    for cap in card.capabilities:
        print(f"  - {cap.name}: {cap.description}")
    print(f"\nMetadata: {card.metadata}")


async def test_orchestrator_integration():
    """Test calling email agent through orchestrator"""
    print("\n" + "="*60)
    print("TEST 4: Orchestrator Integration")
    print("="*60)
    
    try:
        from services.agents.orchestrator_agent import orchestrator_agent
        
        # Test query that should trigger email agent
        query = "Send an email to test@example.com with subject 'Test' and body 'Hello from orchestrator'"
        
        result = await orchestrator_agent.process_query(
            query=query,
            user_id="test_admin",
            role="admin"
        )
        
        print(f"\nOrchestrator Response:")
        print(f"Success: {result.get('success')}")
        print(f"Response: {result.get('response')}")
        print(f"Agents Used: {result.get('agents_used')}")
        
        if result.get('success'):
            print(f"\n✅ Orchestrator successfully coordinated with email agent!")
        else:
            print(f"\n❌ Error: {result.get('error')}")
            
    except Exception as e:
        print(f"\n❌ Error testing orchestrator integration: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("EMAIL AGENT A2A INTEGRATION TESTS")
    print("="*60)
    
    try:
        await test_agent_card()
        await test_send_expense_notification()
        await test_send_generic_email()
        await test_orchestrator_integration()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
