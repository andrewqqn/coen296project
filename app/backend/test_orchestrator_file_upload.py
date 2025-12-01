#!/usr/bin/env python3
"""
Test script for orchestrator file upload workflow
Tests both emulator and production modes
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.multi_agent_orchestrator import process_query_with_agents
from fastapi import UploadFile
from io import BytesIO


async def test_file_upload_workflow():
    """Test the complete file upload and expense creation workflow"""
    
    print("=" * 80)
    print("Testing Orchestrator File Upload Workflow")
    print("=" * 80)
    
    # Test 1: Query with file path (simulating uploaded file)
    print("\n[TEST 1] Testing query with file path reference")
    print("-" * 80)
    
    query_with_file = """Create an expense from this receipt

Attached files:
- Receipt PDF uploaded at: local://uploads/receipts/emp_test/sample_receipt.pdf"""
    
    print(f"Query: {query_with_file}")
    print("\nProcessing...")
    
    result = await process_query_with_agents(
        query=query_with_file,
        employee_id="emp_test",
        role="employee"
    )
    
    print(f"\nResult:")
    print(f"  Success: {result.get('success')}")
    print(f"  Response: {result.get('response')}")
    print(f"  Agents Used: {result.get('agents_used')}")
    if result.get('error'):
        print(f"  Error: {result.get('error')}")
    
    # Test 2: Query without file (should explain what's needed)
    print("\n" + "=" * 80)
    print("[TEST 2] Testing query without file")
    print("-" * 80)
    
    query_no_file = "Create an expense from a receipt"
    
    print(f"Query: {query_no_file}")
    print("\nProcessing...")
    
    result = await process_query_with_agents(
        query=query_no_file,
        employee_id="emp_test",
        role="employee"
    )
    
    print(f"\nResult:")
    print(f"  Success: {result.get('success')}")
    print(f"  Response: {result.get('response')}")
    print(f"  Agents Used: {result.get('agents_used')}")
    if result.get('error'):
        print(f"  Error: {result.get('error')}")
    
    # Test 3: Simulate actual file upload
    print("\n" + "=" * 80)
    print("[TEST 3] Testing with actual file upload simulation")
    print("-" * 80)
    
    # Create a mock PDF file
    mock_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
    mock_file = UploadFile(
        filename="test_receipt.pdf",
        file=BytesIO(mock_pdf_content)
    )
    
    query_upload = "Extract information from this receipt and create an expense"
    
    print(f"Query: {query_upload}")
    print(f"File: {mock_file.filename}")
    print("\nProcessing...")
    
    result = await process_query_with_agents(
        query=query_upload,
        employee_id="emp_test",
        role="employee",
        files=[mock_file]
    )
    
    print(f"\nResult:")
    print(f"  Success: {result.get('success')}")
    print(f"  Response: {result.get('response')[:200]}..." if result.get('response') else "  Response: None")
    print(f"  Agents Used: {result.get('agents_used')}")
    if result.get('error'):
        print(f"  Error: {result.get('error')}")
    
    print("\n" + "=" * 80)
    print("Tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_file_upload_workflow())
