import os
import firebase_admin
import logging # Import the logging library
from firebase_admin import credentials, firestore, storage
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Configure basic logging
logging.basicConfig(level=logging.INFO)

class ExpenseAgent:
    """Handles expense-related tasks, such as creating, updating, and deleting expenses."""
    def __init__(self):
        self.db = firestore.client()

    def create_expense(self, data):
        """Creates a new expense in Firestore."""
        try:
            self.db.collection("expenses").add(data)
            return {"success": True}
        except Exception as e:
            logging.error(f"[Firestore] Error creating expense: {e}") # Enhanced logging
            return {"error": f"Error creating expense: {e}"}

    def list_expenses(self, is_admin=False, user_id=None):
        """Retrieves expenses from Firestore."""
        try:
            query = self.db.collection("expenses")
            if not is_admin and user_id:
                query = query.where("user_id", "==", user_id)
            
            expenses_ref = query.stream()
            expenses = []
            for expense in expenses_ref:
                expense_data = expense.to_dict()
                expense_data['id'] = expense.id
                expenses.append(expense_data)
            return expenses
        except Exception as e:
            logging.error(f"[Firestore] Error listing expenses: {e}") # Enhanced logging
            return {"error": f"Error listing expenses: {e}"}

    def get_expense(self, expense_id):
        """Retrieves a single expense from Firestore."""
        try:
            expense_ref = self.db.collection("expenses").document(expense_id)
            expense = expense_ref.get()
            if expense.exists:
                return expense.to_dict()
            else:
                return None
        except Exception as e:
            logging.error(f"[Firestore] Error getting expense: {e}") # Enhanced logging
            return {"error": f"Error getting expense: {e}"}

    def update_expense_status(self, expense_id, status):
        """Updates the status of an expense in Firestore."""
        try:
            self.db.collection("expenses").document(expense_id).update({"status": status})
            return {"success": True}
        except Exception as e:
            logging.error(f"[Firestore] Error updating expense status: {e}") # Enhanced logging
            return {"error": f"Error updating expense status: {e}"}

class DocMgmtAgent:
    """Handles document management tasks from Firebase Storage."""
    def __init__(self, bucket_name):
        self.bucket = storage.bucket(name=bucket_name)

    def upload_document(self, file):
        """Uploads a document to Firebase Storage and returns its URL and path."""
        if not file:
            return {"error": "No file provided."}

        if file.content_length > 5 * 1024 * 1024:
            return {"error": "File size exceeds the 5MB limit."}

        try:
            file_path = f"invoices/{file.filename}"
            blob = self.bucket.blob(file_path)
            blob.upload_from_file(file, content_type=file.content_type)
            blob.make_public()
            return {"public_url": blob.public_url, "file_path": file_path}
        except Exception as e:
            logging.error(f"[Storage] Error uploading document: {e}") # Enhanced logging
            return {"error": f"Error uploading document: {e}"}

    def delete_document(self, file_path):
        """Deletes a document from Firebase Storage."""
        if not file_path:
            return {"error": "No file path provided."}
        try:
            blob = self.bucket.blob(file_path)
            if blob.exists():
                blob.delete()
                return {"success": True}
            else:
                return {"error": "Document not found, could not delete."}
        except Exception as e:
            logging.error(f"[Storage] Error deleting document: {e}") # Enhanced logging
            return {"error": f"Error deleting document: {e}"}

class EmailAgent:
    """Handles email-related tasks, such as sending notifications."""
    def __init__(self):
        self.sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        self.sender_email = os.environ.get('SENDER_EMAIL')

    def send_email(self, to_email, subject, html_content):
        """Sends an email to the specified recipient using SendGrid."""
        if not self.sendgrid_api_key or not self.sender_email:
            return "SendGrid API key or sender email not configured."

        message = Mail(
            from_email=self.sender_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content)
        try:
            sg = SendGridAPIClient(self.sendgrid_api_key)
            response = sg.send(message)
            return f"Email sent to {to_email}. Status code: {response.status_code}"
        except Exception as e:
            logging.error(f"[SendGrid] Error sending email: {e}") # Enhanced logging
            return f"Error sending email: {e}"

class PolicyRAG:
    """Provides policy information using a retrieval-augmented generation (RAG) approach."""
    def __init__(self):
        self.vector_db = {
            "expense limits": "The expense limit for meals is $50.",
            "travel policy": "All travel must be pre-approved by your manager."
        }

    def get__policy(self, query):
        """Retrieves the relevant policy based on the user's query."""
        for key in self.vector_db:
            if key in query:
                return self.vector_db[key]
        return "Policy not found."

class OrchestratorAgent:
    """Handles task scheduling and manages the conversation context."""
    def __init__(self, expense_agent, doc_mgmt_agent, email_agent, policy_rag):
        self.expense_agent = expense_agent
        self.doc_mgmt_agent = doc_mgmt_agent
        self.email_agent = email_agent
        self.policy_rag = policy_rag

    def process_request(self, request_text):
        """Processes the user's request and delegates to the appropriate agent."""
        if "create expense" in request_text:
            expense_data = {"item": "lunch", "amount": 25}
            return self.expense_agent.create_expense(expense_data)
        elif "policy" in request_text:
            return self.policy_rag.get_policy(request_text)
        elif "send email" in request_text:
            return self.email_agent.send_email("test@example.com", "Test", "This is a test.")
        else:
            return "I'm not sure how to handle that request."
