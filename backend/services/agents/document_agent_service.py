"""
Document Agent - Handles document processing and information extraction
"""
import os
import json
import base64
import logging
from io import BytesIO
from typing import Dict, Any, Optional
from pdf2image import convert_from_bytes
from openai import AsyncOpenAI

from services.agents.base_agent import BaseAgent
from services.agents.a2a_protocol import (
    AgentCard,
    AgentCapability,
    A2ARequest,
    A2AResponse
)

logger = logging.getLogger("document_agent")
logger.setLevel(logging.INFO)

client = AsyncOpenAI()


class DocumentAgent(BaseAgent):
    """
    Document Agent - Processes documents and extracts structured information
    """
    
    def __init__(self):
        super().__init__(
            agent_id="document_agent",
            name="Document Processing Agent",
            description="Processes PDF receipts and extracts structured information using AI vision"
        )
    
    def get_agent_card(self) -> AgentCard:
        """Return the agent's capability card"""
        return AgentCard(
            agent_id=self.agent_id,
            name=self.name,
            description=self.description,
            version="1.0.0",
            capabilities=[
                AgentCapability(
                    name="extract_receipt_info",
                    description="Extract structured information from a receipt PDF",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the PDF file (local:// or remote URL)"
                            },
                            "extract_fields": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Fields to extract (vendor, amount, date, category, description)",
                                "default": ["vendor", "amount", "date", "category", "description"]
                            }
                        },
                        "required": ["file_path"]
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "vendor": {"type": "string"},
                            "amount": {"type": "number"},
                            "date": {"type": "string"},
                            "category": {"type": "string"},
                            "description": {"type": "string"},
                            "raw_text": {"type": "string"}
                        }
                    }
                ),
                AgentCapability(
                    name="convert_pdf_to_images",
                    description="Convert a PDF document to base64-encoded JPEG images",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the PDF file"
                            },
                            "dpi": {
                                "type": "integer",
                                "description": "DPI for image conversion",
                                "default": 100
                            }
                        },
                        "required": ["file_path"]
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "images": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Base64-encoded JPEG images"
                            },
                            "page_count": {"type": "integer"}
                        }
                    }
                )
            ],
            metadata={
                "model": "gpt-4o-mini",
                "supports_vision": True,
                "supported_formats": ["pdf"],
                "max_file_size_mb": 10
            }
        )
    
    async def handle_request(self, request: A2ARequest, context: Dict[str, Any]) -> A2AResponse:
        """Handle incoming A2A requests"""
        try:
            capability = request.capability_name
            params = request.parameters
            
            if capability == "extract_receipt_info":
                file_path = params.get("file_path")
                extract_fields = params.get("extract_fields", ["vendor", "amount", "date", "category", "description"])
                
                if not file_path:
                    return A2AResponse(
                        success=False,
                        error="Missing required parameter: file_path"
                    )
                
                result = await self._extract_receipt_info(file_path, extract_fields)
                
                # Check if result contains an error
                if isinstance(result, dict) and result.get("success") == False:
                    return A2AResponse(success=False, error=result.get("error", "Unknown error"))
                
                return A2AResponse(success=True, result=result)
            
            elif capability == "convert_pdf_to_images":
                file_path = params.get("file_path")
                dpi = params.get("dpi", 100)
                
                if not file_path:
                    return A2AResponse(
                        success=False,
                        error="Missing required parameter: file_path"
                    )
                
                result = await self._convert_pdf_to_images(file_path, dpi)
                
                # Check if result contains an error
                if isinstance(result, dict) and result.get("success") == False:
                    return A2AResponse(success=False, error=result.get("error", "Unknown error"))
                
                return A2AResponse(success=True, result=result)
            
            else:
                return A2AResponse(
                    success=False,
                    error=f"Unknown capability: {capability}"
                )
                
        except Exception as e:
            logger.error(f"Error handling request in DocumentAgent: {str(e)}", exc_info=True)
            return A2AResponse(
                success=False,
                error=str(e)
            )
    
    async def _extract_receipt_info(self, file_path: str, extract_fields: list) -> Dict[str, Any]:
        """Extract structured information from a receipt"""
        try:
            # Read PDF file
            pdf_bytes = self._read_file(file_path)
            
            # Convert to images
            pages = convert_from_bytes(pdf_bytes, dpi=100)
            if not pages:
                raise ValueError("PDF converted to zero pages")
            
            # Convert first page to base64
            img = pages[0]
            buf = BytesIO()
            img.save(buf, format="JPEG")
            jpeg_bytes = buf.getvalue()
            base64_image = base64.b64encode(jpeg_bytes).decode("utf-8")
            
            logger.info(f"Converted PDF to {len(pages)} page(s), analyzing first page")
            
            # Use OpenAI vision to extract information
            fields_str = ", ".join(extract_fields)
            prompt = f"""Analyze this receipt image and extract the following information: {fields_str}

For each field:
- vendor: The merchant/vendor name
- amount: Just the number, no currency symbol (e.g., 93.50)
- date: In YYYY-MM-DD format if possible
- category: Choose one: meals, transportation, office_supplies, lodging, entertainment, other
- description: One sentence summary

Return ONLY a valid JSON object with these keys. Do not include markdown or code blocks."""
            
            response = await client.responses.create(
                model="gpt-4o-mini",
                input=[
                    {"role": "system", "content": [{"type": "input_text", "text": "You are a receipt analysis assistant. Extract structured data and return only valid JSON."}]},
                    {"role": "user", "content": [
                        {"type": "input_image", "image_url": f"data:image/jpeg;base64,{base64_image}"},
                        {"type": "input_text", "text": prompt}
                    ]}
                ]
            )
            
            extracted_text = response.output_text.strip()
            logger.info(f"OpenAI response: {extracted_text}")
            
            # Parse JSON response
            try:
                extracted_info = json.loads(extracted_text)
            except json.JSONDecodeError:
                logger.warning("Response wasn't valid JSON")
                extracted_info = {"raw_text": extracted_text}
            
            return extracted_info
            
        except Exception as e:
            logger.error(f"Error extracting receipt info: {str(e)}", exc_info=True)
            # Return error dict instead of raising
            return {
                "success": False,
                "error": f"Failed to extract receipt info: {str(e)}"
            }
    
    async def _convert_pdf_to_images(self, file_path: str, dpi: int) -> Dict[str, Any]:
        """Convert PDF to base64-encoded images"""
        try:
            pdf_bytes = self._read_file(file_path)
            pages = convert_from_bytes(pdf_bytes, dpi=dpi)
            
            if not pages:
                raise ValueError("PDF converted to zero pages")
            
            images = []
            for page in pages:
                buf = BytesIO()
                page.save(buf, format="JPEG")
                jpeg_bytes = buf.getvalue()
                base64_str = base64.b64encode(jpeg_bytes).decode("utf-8")
                images.append(base64_str)
            
            return {
                "images": images,
                "page_count": len(images)
            }
            
        except Exception as e:
            logger.error(f"Error converting PDF: {str(e)}", exc_info=True)
            # Return error dict instead of raising
            return {
                "success": False,
                "error": f"Failed to convert PDF: {str(e)}"
            }
    
    def _read_file(self, file_path: str) -> bytes:
        """Read file from local or remote path"""
        logger.info(f"Reading file: {file_path}")
        
        if file_path.startswith("local://"):
            local_path = file_path.replace("local://", "")
            full_path = os.path.join(os.getcwd(), local_path)
            
            logger.info(f"Resolved to full path: {full_path}")
            
            if not os.path.exists(full_path):
                error_msg = f"File not found: {full_path}"
                logger.error(error_msg)
                # Check if directory exists
                dir_path = os.path.dirname(full_path)
                if os.path.exists(dir_path):
                    logger.info(f"Directory exists: {dir_path}")
                    logger.info(f"Files in directory: {os.listdir(dir_path)}")
                else:
                    logger.error(f"Directory does not exist: {dir_path}")
                raise FileNotFoundError(error_msg)
            
            logger.info(f"File exists, size: {os.path.getsize(full_path)} bytes")
            
            with open(full_path, 'rb') as f:
                data = f.read()
                logger.info(f"Successfully read {len(data)} bytes")
                return data
        else:
            # TODO: Implement remote file download
            raise NotImplementedError("Remote file download not yet implemented")


# Legacy function for backward compatibility
def extract_receipt_info(receipt_text: str):
    """Legacy function - kept for backward compatibility"""
    return {"parsed_info": receipt_text}


# Create and register the document agent
document_agent = DocumentAgent()
document_agent.register()
