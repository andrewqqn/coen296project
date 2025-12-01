"""
Base Agent class for A2A protocol
"""
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from pydantic_ai import Agent as PydanticAgent
from pydantic_ai.models.openai import OpenAIResponsesModel

from .a2a_protocol import (
    AgentCard,
    A2AMessage,
    A2ARequest,
    A2AResponse,
    agent_registry
)
from utils.logger import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    Base class for all agents in the system.
    Handles A2A protocol communication and Pydantic AI integration.
    """
    
    def __init__(self, agent_id: str, name: str, description: str):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.card: Optional[AgentCard] = None
        self.pydantic_agent: Optional[PydanticAgent] = None
        
    @abstractmethod
    def get_agent_card(self) -> AgentCard:
        """Return the agent's capability card"""
        pass
    
    @abstractmethod
    async def handle_request(self, request: A2ARequest, context: Dict[str, Any]) -> A2AResponse:
        """Handle an incoming A2A request"""
        pass
    
    def register(self):
        """Register this agent with the global registry"""
        self.card = self.get_agent_card()
        agent_registry.register_agent(self.card)
        logger.info(f"Registered agent: {self.name} ({self.agent_id})")
    
    async def process_message(self, message: A2AMessage, context: Dict[str, Any]) -> A2AMessage:
        """
        Process an incoming A2A message and return a response message
        """
        try:
            if message.message_type != "request":
                return self._create_error_message(
                    message,
                    "Only request messages are supported"
                )
            
            # Extract request from payload
            request = A2ARequest(**message.payload)
            
            # Handle the request
            response = await self.handle_request(request, context)
            
            # Create response message
            return A2AMessage(
                sender_agent_id=self.agent_id,
                recipient_agent_id=message.sender_agent_id,
                message_type="response",
                capability_name=message.capability_name,
                payload=response.dict(),
                correlation_id=message.correlation_id or message.message_id
            )
            
        except Exception as e:
            logger.error(f"Error processing message in {self.name}: {str(e)}", exc_info=True)
            return self._create_error_message(message, str(e))
    
    def _create_error_message(self, original_message: A2AMessage, error: str) -> A2AMessage:
        """Create an error response message"""
        return A2AMessage(
            sender_agent_id=self.agent_id,
            recipient_agent_id=original_message.sender_agent_id,
            message_type="error",
            capability_name=original_message.capability_name,
            payload={
                "success": False,
                "error": error
            },
            correlation_id=original_message.correlation_id or original_message.message_id
        )
    
    def create_pydantic_agent(self, system_prompt: str, model_name: str = "gpt-4o-mini") -> PydanticAgent:
        """Create a Pydantic AI agent for this agent"""
        model = OpenAIResponsesModel(model_name)
        self.pydantic_agent = PydanticAgent(
            model=model,
            system_prompt=system_prompt
        )
        return self.pydantic_agent
