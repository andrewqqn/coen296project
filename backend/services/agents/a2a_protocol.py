"""
A2A (Agent-to-Agent) Protocol Implementation
Based on Google's A2A protocol for multi-agent communication
"""
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class AgentCapability(BaseModel):
    """Describes a single capability of an agent"""
    name: str = Field(..., description="Name of the capability")
    description: str = Field(..., description="What this capability does")
    input_schema: Dict[str, Any] = Field(..., description="JSON schema for input parameters")
    output_schema: Dict[str, Any] = Field(..., description="JSON schema for output")


class AgentCard(BaseModel):
    """
    Agent Card - Advertises an agent's capabilities
    Similar to OpenAPI spec but for agents
    """
    agent_id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="What this agent does")
    version: str = Field(default="1.0.0", description="Agent version")
    capabilities: List[AgentCapability] = Field(..., description="List of capabilities")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class A2AMessage(BaseModel):
    """Message format for agent-to-agent communication"""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sender_agent_id: str = Field(..., description="ID of the sending agent")
    recipient_agent_id: str = Field(..., description="ID of the receiving agent")
    message_type: Literal["request", "response", "error"] = Field(..., description="Type of message")
    capability_name: Optional[str] = Field(None, description="Capability being invoked")
    payload: Dict[str, Any] = Field(..., description="Message payload")
    correlation_id: Optional[str] = Field(None, description="For tracking request-response pairs")


class A2ARequest(BaseModel):
    """Request from one agent to another"""
    capability_name: str = Field(..., description="Name of capability to invoke")
    parameters: Dict[str, Any] = Field(..., description="Input parameters")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")


class A2AResponse(BaseModel):
    """Response from an agent"""
    success: bool = Field(..., description="Whether the request succeeded")
    result: Optional[Dict[str, Any]] = Field(None, description="Result data")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AgentRegistry:
    """Registry for managing agent cards and routing"""
    
    def __init__(self):
        self._agents: Dict[str, AgentCard] = {}
    
    def register_agent(self, card: AgentCard):
        """Register an agent with its card"""
        self._agents[card.agent_id] = card
    
    def get_agent_card(self, agent_id: str) -> Optional[AgentCard]:
        """Get an agent's card by ID"""
        return self._agents.get(agent_id)
    
    def list_agents(self) -> List[AgentCard]:
        """List all registered agents"""
        return list(self._agents.values())
    
    def find_agents_by_capability(self, capability_name: str) -> List[AgentCard]:
        """Find agents that have a specific capability"""
        matching_agents = []
        for card in self._agents.values():
            for cap in card.capabilities:
                if cap.name == capability_name:
                    matching_agents.append(card)
                    break
        return matching_agents
    
    def get_all_capabilities(self) -> Dict[str, List[str]]:
        """Get a map of all capabilities to agent IDs"""
        capabilities_map = {}
        for card in self._agents.values():
            for cap in card.capabilities:
                if cap.name not in capabilities_map:
                    capabilities_map[cap.name] = []
                capabilities_map[cap.name].append(card.agent_id)
        return capabilities_map


# Global registry instance
agent_registry = AgentRegistry()


def create_a2a_message(
    sender_id: str,
    recipient_id: str,
    message_type: Literal["request", "response", "error"],
    payload: Dict[str, Any],
    capability_name: Optional[str] = None,
    correlation_id: Optional[str] = None
) -> A2AMessage:
    """Helper to create A2A messages"""
    return A2AMessage(
        sender_agent_id=sender_id,
        recipient_agent_id=recipient_id,
        message_type=message_type,
        capability_name=capability_name,
        payload=payload,
        correlation_id=correlation_id
    )
