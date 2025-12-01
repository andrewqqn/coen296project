"""
Email Agent - Handles email notifications and communication using A2A protocol
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.agents.base_agent import BaseAgent
from services.agents.a2a_protocol import (
    AgentCard,
    AgentCapability,
    A2ARequest,
    A2AResponse
)

logger = logging.getLogger("email_agent")
logger.setLevel(logging.INFO)


class EmailAgent(BaseAgent):
    """
    Email Agent - Sends notifications and manages email communication
    """
    
    def __init__(self):
        super().__init__(
            agent_id="email_agent",
            name="Email Notification Agent",
            description="Sends email notifications for expense decisions and system events"
        )
        self._email_service = None

    def _get_email_service(self):
        """Lazy load email service to avoid circular imports"""
        if self._email_service is None:
            logger.info("[EMAIL SERVICE] Initializing email service...")
            try:
                # Check if Gmail token exists
                import os
                # Get absolute path to token file
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
                token_path = os.path.join(project_root, 'app', 'gmail_token.json')
                credentials_path = os.path.join(project_root, 'app', 'gmail_oauth_credentials.json')
                logger.info(f"[Gmail] Looking for token at: {token_path}")
                logger.info(f"[Gmail] Token exists: {os.path.exists(token_path)}")
                
                if os.path.exists(token_path):
                    # Use Gmail!
                    logger.info("🔧 Initializing Gmail service...")
                    
                    # Add agents directory to path temporarily so `email_agent` package can be imported
                    import sys
                    agents_dir = os.path.join(project_root, 'app', 'services', 'agents')
                    if agents_dir not in sys.path:
                        logger.info(f"[Gmail] Adding agents_dir to sys.path: {agents_dir}")
                        sys.path.insert(0, agents_dir)
                    # Ensure project root is also available as a fallback (allows importing via `backend.*` if needed)
                    if project_root not in sys.path:
                        logger.info(f"[Gmail] Adding project_root to sys.path: {project_root}")
                        sys.path.insert(0, project_root)

                    from email_agent.gmail.gmail_service_creator import GmailServiceCreator
                    from email_agent.gmail.gmail_client import GmailClient
                    from email_agent.services.email_service import EmailService
                    
                    # Create Gmail service
                    service = GmailServiceCreator.create_gmail_service(
                        credentials_file=credentials_path,
                        token_file=token_path
                    )
                    
                    # Wrap in email service
                    gmail_client = GmailClient(service)
                    email_service = EmailService(gmail_client)
                    
                    # Adapt to our interface - wrap Gmail response to match expected format
                    def send_wrapper(to, subject, body):
                        gmail_result = email_service.send_email(to, subject, body)
                        # Gmail returns {"id": "...", "threadId": "..."}
                        # Convert to our expected format
                        return {
                            "message_id": gmail_result.get("id", "unknown"),
                            "thread_id": gmail_result.get("threadId"),
                            "status": "sent",
                            "to": to
                        }
                    
                    self._email_service = {"send": send_wrapper}
                    
                    logger.info("✅ Gmail service initialized - REAL emails will be sent!")
                else:
                    # Fallback to mock
                    from infrastructure.email_client import send_email
                    self._email_service = {"send": send_email}
                    logger.info("⚠️  Gmail token not found, using mock email service")
                    
            except Exception as e:
                # Fallback to mock on any error
                logger.error(f"Gmail initialization failed: {e}, using mock", exc_info=True)
                from infrastructure.email_client import send_email
                self._email_service = {"send": send_email}
    
        return self._email_service
    
    def get_agent_card(self) -> AgentCard:
        """Return the agent's capability card"""
        return AgentCard(
            agent_id=self.agent_id,
            name=self.name,
            description=self.description,
            version="1.0.0",
            capabilities=[
                AgentCapability(
                    name="send_expense_notification",
                    description="Send email notification about expense decision",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "to": {
                                "type": "string",
                                "description": "Recipient email address"
                            },
                            "expense_id": {
                                "type": "string",
                                "description": "The expense ID"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["approved", "rejected", "admin_review", "pending"],
                                "description": "The expense status"
                            },
                            "amount": {
                                "type": "number",
                                "description": "The expense amount"
                            },
                            "category": {
                                "type": "string",
                                "description": "The expense category"
                            },
                            "decision_reason": {
                                "type": "string",
                                "description": "Reason for the decision"
                            }
                        },
                        "required": ["to", "expense_id", "status", "amount"]
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "sent": {"type": "boolean"},
                            "message_id": {"type": "string"}
                        }
                    }
                ),
                AgentCapability(
                    name="send_email",
                    description="Send a generic email",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "to": {
                                "type": "string",
                                "description": "Recipient email address"
                            },
                            "subject": {
                                "type": "string",
                                "description": "Email subject"
                            },
                            "body": {
                                "type": "string",
                                "description": "Email body content"
                            }
                        },
                        "required": ["to", "subject", "body"]
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "sent": {"type": "boolean"},
                            "message_id": {"type": "string"}
                        }
                    }
                ),
                AgentCapability(
                    name="search_emails",
                    description="Search emails in inbox (requires Gmail integration)",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (Gmail search syntax)"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 50
                            }
                        },
                        "required": ["query"]
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "messages": {
                                "type": "array",
                                "items": {"type": "object"}
                            },
                            "count": {"type": "integer"}
                        }
                    }
                )
            ],
            metadata={
                "supports_gmail": False,  # Set to True when Gmail is configured
                "notification_types": ["expense_decision", "generic"]
            }
        )
    
    async def handle_request(self, request: A2ARequest, context: Dict[str, Any]) -> A2AResponse:
        """Handle incoming A2A requests"""
        try:
            capability = request.capability_name
            params = request.parameters
            
            if capability == "send_expense_notification":
                result = await self._send_expense_notification(params)
                return A2AResponse(success=True, result=result)
            
            elif capability == "send_email":
                result = await self._send_email(params)
                return A2AResponse(success=True, result=result)
            
            elif capability == "search_emails":
                result = await self._search_emails(params)
                return A2AResponse(success=True, result=result)
            
            else:
                return A2AResponse(
                    success=False,
                    error=f"Unknown capability: {capability}"
                )
                
        except Exception as e:
            logger.error(f"Error handling request in EmailAgent: {str(e)}", exc_info=True)
            return A2AResponse(
                success=False,
                error=str(e)
            )
    
    async def _send_expense_notification(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send expense decision notification email"""
        to = params.get("to")
        expense_id = params.get("expense_id")
        status = params.get("status")
        amount = params.get("amount")
        category = params.get("category", "N/A")
        decision_reason = params.get("decision_reason", "N/A")
        
        # Build email content
        subject = f"Expense Request #{expense_id} - {status.upper()}"
        
        status_emoji = {
            "approved": "✅",
            "rejected": "❌",
            "admin_review": "⏳",
            "pending": "🔄"
        }.get(status, "📧")
        
        body = f"""
{status_emoji} Expense Request Update

Hello,

Your expense request has been processed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Expense Details
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Expense ID:     {expense_id}
Status:         {status.upper()}
Amount:         ${amount:.2f}
Category:       {category}

Decision Reason:
{decision_reason}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        if status == "approved":
            body += """
✅ Your expense has been APPROVED and the reimbursement will be processed.
The amount will be credited to your registered bank account.

"""
        elif status == "rejected":
            body += """
❌ Your expense has been REJECTED.
Please review the decision reason above and contact your manager if you have questions.

"""
        elif status == "admin_review":
            body += """
⏳ Your expense requires MANUAL REVIEW by an administrator.
You will receive another notification once the review is complete.

"""
        
        body += f"""
Processed:      {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Thank you,
ExpenseSense Reimbursement System

This is an automated notification. Please do not reply to this email.
"""
        
        # Send email
        email_service = self._get_email_service()
        result = email_service["send"](to=to, subject=subject, body=body)
        
        logger.info(f"Sent expense notification to {to} for expense {expense_id}")
        
        return {
            "sent": True,
            "message_id": result.get("message_id", "mock_id"),
            "to": to,
            "subject": subject
        }
    
    async def _send_email(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a generic email"""
        to = params.get("to")
        subject = params.get("subject")
        body = params.get("body")
        
        if not all([to, subject, body]):
            raise ValueError("Missing required parameters: to, subject, body")
        
        email_service = self._get_email_service()
        result = email_service["send"](to=to, subject=subject, body=body)
        
        logger.info(f"Sent email to {to}: {subject}")
        
        return {
            "sent": True,
            "message_id": result.get("message_id", "mock_id"),
            "to": to,
            "subject": subject
        }
    
    async def _search_emails(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search emails (requires Gmail integration)"""
        query = params.get("query", "")
        max_results = params.get("max_results", 50)
        
        logger.info(f"Email search requested: {query}")
        
        # This would require Gmail client setup
        # For now, return mock response
        return {
            "messages": [],
            "count": 0,
            "note": "Gmail integration not configured. This is a mock response."
        }


# Create and register the email agent
email_agent = EmailAgent()
email_agent.register()
