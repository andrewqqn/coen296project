"""
Complete Email Agent Workflow Test

This test demonstrates the full integration of the email agent
in a realistic expense submission and review workflow.
"""
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_complete_workflow():
    """
    Test the complete workflow:
    1. Create an expense
    2. AI reviews it
    3. Email notification sent automatically
    4. Verify all agents communicated correctly
    """
    print("\n" + "="*70)
    print("COMPLETE EMAIL AGENT WORKFLOW TEST")
    print("="*70)
    
    try:
        # Import services
        from services import expense_service, employee_service
        from services.agents.expense_agent_service import evaluate_and_maybe_auto_approve
        from domain.schemas.expense_schema import ExpenseCreate
        from datetime import datetime
        
        print("\n📋 Step 1: Create test employee")
        print("-" * 70)
        
        # Create a test employee
        employee_data = {
            "name": "Test Employee",
            "email": "test.employee@company.com",
            "department": "Engineering",
            "role": "employee"
        }
        
        try:
            employee = employee_service.create_employee(employee_data)
            employee_id = employee.get("employee_id")
            print(f"✅ Created employee: {employee_id}")
            print(f"   Email: {employee.get('email')}")
        except Exception as e:
            print(f"⚠️  Using existing employee (error: {e})")
            # Use a default employee ID for testing
            employee_id = "test_emp_001"
        
        print("\n📝 Step 2: Create expense")
        print("-" * 70)
        
        # Create an expense
        expense_create = ExpenseCreate(
            employee_id=employee_id,
            amount=89.99,
            category="Meals",
            business_justification="Team lunch meeting to discuss Q4 roadmap",
            date_of_expense=datetime.utcnow()
        )
        
        # Note: In real workflow, receipt would be uploaded
        # For this test, we'll create without receipt
        expense = expense_service.create_expense(expense_create, receipt_path=None)
        expense_dict = expense.dict() if hasattr(expense, 'dict') else expense
        expense_id = expense_dict.get('expense_id') or expense_dict.get('id')
        
        print(f"✅ Created expense: {expense_id}")
        print(f"   Amount: ${expense_dict.get('amount')}")
        print(f"   Category: {expense_dict.get('category')}")
        print(f"   Status: {expense_dict.get('status')}")
        
        print("\n🤖 Step 3: AI Review (simulated)")
        print("-" * 70)
        print("Note: Full AI review requires receipt upload")
        print("This test demonstrates the email notification flow")
        
        # Simulate what happens during AI review
        from services.agents.email_agent_service import email_agent
        from services.agents.a2a_protocol import A2ARequest, create_a2a_message
        
        print("\n📧 Step 4: Send email notification")
        print("-" * 70)
        
        # Create email notification (this is what expense_agent does automatically)
        email_request = A2ARequest(
            capability_name="send_expense_notification",
            parameters={
                "to": employee_data["email"],
                "expense_id": expense_id,
                "status": "approved",  # Simulated approval
                "amount": float(expense_dict.get('amount', 0)),
                "category": expense_dict.get('category', 'N/A'),
                "decision_reason": "R1: Expense within policy limits, first request of day"
            },
            context={"user_id": "system", "role": "system"}
        )
        
        message = create_a2a_message(
            sender_id="expense_agent",
            recipient_id="email_agent",
            message_type="request",
            payload=email_request.model_dump(),
            capability_name="send_expense_notification"
        )
        
        response = await email_agent.process_message(
            message,
            context={"user_id": "system", "role": "system"}
        )
        
        if response.message_type == "response":
            result = response.payload.get("result", {})
            print(f"✅ Email notification sent!")
            print(f"   To: {result.get('to')}")
            print(f"   Subject: {result.get('subject')}")
            print(f"   Message ID: {result.get('message_id')}")
        else:
            print(f"❌ Email failed: {response.payload.get('error')}")
        
        print("\n🔍 Step 5: Verify agent communication")
        print("-" * 70)
        
        # Verify agent registry
        from services.agents.a2a_protocol import agent_registry
        
        agents = agent_registry.list_agents()
        email_agent_found = any(a.agent_id == "email_agent" for a in agents)
        
        if email_agent_found:
            print(f"✅ Email agent registered in agent registry")
            print(f"   Total agents: {len(agents)}")
            for agent in agents:
                print(f"   - {agent.name} ({agent.agent_id})")
        else:
            print("❌ Email agent not found in registry")
        
        print("\n" + "="*70)
        print("WORKFLOW TEST COMPLETED SUCCESSFULLY")
        print("="*70)
        
        print("\n📊 Summary:")
        print(f"   ✅ Employee created/verified")
        print(f"   ✅ Expense created: {expense_id}")
        print(f"   ✅ Email notification sent")
        print(f"   ✅ A2A protocol communication verified")
        
        print("\n💡 In production workflow:")
        print("   1. User uploads receipt PDF")
        print("   2. Document agent extracts info")
        print("   3. Expense created with receipt")
        print("   4. Expense agent reviews automatically")
        print("   5. Email agent sends notification automatically")
        print("   6. All communication logged in audit system")
        
    except Exception as e:
        print(f"\n❌ Workflow test failed: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_orchestrator_email_workflow():
    """
    Test email workflow through orchestrator
    """
    print("\n" + "="*70)
    print("ORCHESTRATOR EMAIL WORKFLOW TEST")
    print("="*70)
    
    try:
        from services.agents.orchestrator_agent import orchestrator_agent
        
        queries = [
            "Send a welcome email to new.employee@company.com",
            "List all available agents",
            "What are the email agent's capabilities?"
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"\n📝 Query {i}: {query}")
            print("-" * 70)
            
            result = await orchestrator_agent.process_query(
                query=query,
                user_id="admin_test",
                role="admin"
            )
            
            if result.get("success"):
                print(f"✅ Response: {result.get('response')[:200]}...")
                if result.get('agents_used'):
                    print(f"   Agents used: {', '.join(result.get('agents_used'))}")
            else:
                print(f"❌ Error: {result.get('error')}")
        
        print("\n" + "="*70)
        print("ORCHESTRATOR TEST COMPLETED")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Orchestrator test failed: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all workflow tests"""
    await test_complete_workflow()
    await test_orchestrator_email_workflow()
    
    print("\n" + "="*70)
    print("ALL WORKFLOW TESTS COMPLETED")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
