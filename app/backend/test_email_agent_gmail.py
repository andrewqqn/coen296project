"""
Test Email Agent with Gmail
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test():
    print("\n" + "="*70)
    print("Testing Email Agent with Gmail")
    print("="*70)
    
    from services.agents.email_agent_service import email_agent
    from services.agents.a2a_protocol import A2ARequest, create_a2a_message
    
    # Create email request
    print("\n📧 Sending test email via email agent...")
    
    email_request = A2ARequest(
        capability_name="send_expense_notification",
        parameters={
            "to": "nguyen.andrew.quang@gmail.com",
            "expense_id": "test_exp_123",
            "status": "approved",
            "amount": 99.99,
            "category": "Meals",
            "decision_reason": "R1: Test email via Gmail integration"
        },
        context={"user_id": "system", "role": "system"}
    )
    
    message = create_a2a_message(
        sender_id="test",
        recipient_id="email_agent",
        message_type="request",
        payload=email_request.model_dump(),
        capability_name="send_expense_notification"
    )
    
    response = await email_agent.process_message(message, context={})
    
    if response.message_type == "response":
        result = response.payload.get("result", {})
        print(f"\n✅ Email sent successfully!")
        print(f"   To: {result.get('to')}")
        print(f"   Subject: {result.get('subject')}")
        print(f"   Message ID: {result.get('message_id')}")
        print(f"\n📬 Check your inbox at: nguyen.andrew.quang@gmail.com")
    else:
        print(f"\n❌ Email failed: {response.payload.get('error')}")
    
    print("\n" + "="*70)

asyncio.run(test())
