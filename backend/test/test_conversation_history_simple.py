"""
Simple test script for conversation history with the Orchestrator endpoint
Run this after starting the backend server
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
# Replace with your actual Firebase token
FIREBASE_TOKEN = "your_firebase_token_here"

def test_conversation():
    """Test a multi-turn conversation with history"""
    url = f"{BASE_URL}/orchestrator/"
    headers = {
        "Authorization": f"Bearer {FIREBASE_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Keep track of conversation history
    conversation_history = []
    
    # First query
    print("\n" + "="*60)
    print("Query 1: List all employees")
    print("="*60)
    
    data1 = {
        "query": "List all employees",
        "message_history": conversation_history
    }
    
    response1 = requests.post(url, headers=headers, json=data1)
    result1 = response1.json()
    
    if result1['success']:
        print(f"\n✅ Response:\n{result1['response']}\n")
        
        # Add to conversation history
        conversation_history.append({
            "role": "user",
            "content": "List all employees"
        })
        conversation_history.append({
            "role": "assistant",
            "content": result1['response']
        })
    else:
        print(f"\n❌ Error: {result1.get('error')}")
        return
    
    # Second query - references the first
    print("\n" + "="*60)
    print("Query 2: How many are there? (should understand context)")
    print("="*60)
    
    data2 = {
        "query": "How many are there?",
        "message_history": conversation_history
    }
    
    response2 = requests.post(url, headers=headers, json=data2)
    result2 = response2.json()
    
    if result2['success']:
        print(f"\n✅ Response:\n{result2['response']}\n")
        
        # Add to conversation history
        conversation_history.append({
            "role": "user",
            "content": "How many are there?"
        })
        conversation_history.append({
            "role": "assistant",
            "content": result2['response']
        })
    else:
        print(f"\n❌ Error: {result2.get('error')}")
        return
    
    # Third query - further context reference
    print("\n" + "="*60)
    print("Query 3: Tell me about the first one")
    print("="*60)
    
    data3 = {
        "query": "Tell me about the first one",
        "message_history": conversation_history
    }
    
    response3 = requests.post(url, headers=headers, json=data3)
    result3 = response3.json()
    
    if result3['success']:
        print(f"\n✅ Response:\n{result3['response']}\n")
    else:
        print(f"\n❌ Error: {result3.get('error')}")
    
    print("\n" + "="*60)
    print("Conversation History Test Complete!")
    print("="*60)

if __name__ == "__main__":
    print("🚀 Conversation History Test Script")
    print(f"Testing endpoint: {BASE_URL}/orchestrator/")
    print("\nNote: Make sure the backend server is running!")
    print("Update FIREBASE_TOKEN in this script with your actual token.\n")
    
    try:
        test_conversation()
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
