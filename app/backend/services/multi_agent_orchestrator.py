"""
Multi-Agent Orchestrator Service
Uses A2A protocol to coordinate between specialized agents
"""
from typing import Dict, Any, List, Optional
from fastapi import UploadFile
import os
import uuid

from services.agents.orchestrator_agent import orchestrator_agent
from services.agents.a2a_protocol import agent_registry
from utils.logger import get_logger

logger = get_logger(__name__)


async def upload_file_to_storage(file: UploadFile, user_id: str) -> str:
    """
    Upload a file to storage and return the path.
    In emulator mode, saves files locally.
    
    Args:
        file: The uploaded file
        user_id: The user ID for organizing files
        
    Returns:
        Path to the uploaded file
    """
    try:
        from config import USE_FIRESTORE_EMULATOR
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.pdf'
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Read file content
        content = await file.read()
        
        # Check if we're using emulator
        if USE_FIRESTORE_EMULATOR:
            logger.info("Using emulator mode - saving file locally")
            
            # Save file locally for emulator mode
            local_dir = os.path.join(os.getcwd(), "uploads", "receipts", user_id)
            os.makedirs(local_dir, exist_ok=True)
            
            local_path = os.path.join(local_dir, unique_filename)
            
            with open(local_path, 'wb') as f:
                f.write(content)
            
            # Return a local reference
            file_url = f"local://uploads/receipts/{user_id}/{unique_filename}"
            logger.info(f"File saved locally: {local_path}")
            return file_url
        else:
            # Production mode - upload to Firebase Storage
            from infrastructure.firebase_client import get_storage_bucket
            
            storage_path = f"receipts/{user_id}/{unique_filename}"
            bucket = get_storage_bucket()
            blob = bucket.blob(storage_path)
            
            # Upload to Firebase Storage
            blob.upload_from_string(content, content_type=file.content_type or 'application/pdf')
            blob.make_public()
            
            logger.info(f"File uploaded to Firebase Storage: {storage_path}")
            return blob.public_url
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        raise


async def process_query_with_agents(
    query: str,
    employee_id: str,
    role: str = "employee",
    message_history: Optional[List[Dict[str, str]]] = None,
    files: Optional[List[UploadFile]] = None
) -> Dict[str, Any]:
    """
    Process a natural language query using the multi-agent system.
    
    Args:
        query: Natural language query from the user
        employee_id: The employee ID of the user making the request
        role: The user's role (employee or admin)
        message_history: Optional list of previous messages
        files: Optional list of uploaded files (e.g., PDF receipts)
        
    Returns:
        Dictionary containing the response and metadata
    """
    try:
        logger.info(f"Processing query from {role} user {employee_id}: {query}")
        
        # Handle file uploads if present
        uploaded_file_urls = []
        if files and len(files) > 0:
            logger.info(f"Processing {len(files)} uploaded file(s)")
            for file in files:
                if file.filename:
                    logger.info(f"Uploading file: {file.filename}")
                    file_url = await upload_file_to_storage(file, employee_id)
                    uploaded_file_urls.append(file_url)
                    logger.info(f"File uploaded: {file_url}")
            
            # Enhance the query with file information
            if uploaded_file_urls:
                file_info = "\n".join([f"- Receipt PDF uploaded at: {url}" for url in uploaded_file_urls])
                enhanced_query = f"{query}\n\nAttached files:\n{file_info}"
                query = enhanced_query
                logger.info(f"Enhanced query with file info: {enhanced_query}")
        
        # Process the query through the orchestrator agent
        result = await orchestrator_agent.process_query(
            query=query,
            user_id=employee_id,
            role=role
        )
        
        logger.info(f"Query processed. Agents used: {result.get('agents_used', [])}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "response": None,
            "agents_used": []
        }


def list_registered_agents() -> List[Dict[str, Any]]:
    """
    List all registered agents and their capabilities.
    
    Returns:
        List of agent cards with capabilities
    """
    agents = agent_registry.list_agents()
    
    result = []
    for card in agents:
        result.append({
            "agent_id": card.agent_id,
            "name": card.name,
            "description": card.description,
            "version": card.version,
            "capabilities": [
                {
                    "name": cap.name,
                    "description": cap.description,
                    "input_schema": cap.input_schema,
                    "output_schema": cap.output_schema
                }
                for cap in card.capabilities
            ],
            "metadata": card.metadata
        })
    
    return result


def get_agent_card(agent_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the card for a specific agent.
    
    Args:
        agent_id: The agent ID
        
    Returns:
        Agent card or None if not found
    """
    card = agent_registry.get_agent_card(agent_id)
    if not card:
        return None
    
    return {
        "agent_id": card.agent_id,
        "name": card.name,
        "description": card.description,
        "version": card.version,
        "capabilities": [
            {
                "name": cap.name,
                "description": cap.description,
                "input_schema": cap.input_schema,
                "output_schema": cap.output_schema
            }
            for cap in card.capabilities
        ],
        "metadata": card.metadata
    }
