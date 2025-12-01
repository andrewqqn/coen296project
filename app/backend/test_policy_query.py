"""
Test script to verify orchestrator can answer policy questions
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.agents.orchestrator_agent import orchestrator_agent


async def test_policy_queries():
    """Test various policy-related queries"""
    
    test_queries = [
        "What are the reimbursement policies?",
        "What are the expense limits for meals?",
        "What are the approval rules?",
        "Tell me about receipt requirements",
        "What happens if I submit multiple expenses in one day?",
    ]
    
    print("=" * 80)
    print("Testing Orchestrator Policy Query Capability")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}")
        
        result = await orchestrator_agent.process_query(
            query=query,
            user_id="test_user",
            role="employee"
        )
        
        if result.get("success"):
            print(f"\n✅ Success!")
            print(f"\nResponse:\n{result.get('response')}")
            print(f"\nAgents used: {result.get('agents_used', [])}")
        else:
            print(f"\n❌ Error: {result.get('error')}")
        
        print("\n" + "-" * 80)


if __name__ == "__main__":
    asyncio.run(test_policy_queries())
