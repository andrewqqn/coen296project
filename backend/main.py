import os
import sys

# Add the 'src' directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

import firebase_admin
from functools import wraps
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from dotenv import load_dotenv
from firebase_admin import auth
from agents import OrchestratorAgent, ExpenseAgent, DocMgmtAgent, EmailAgent, PolicyRAG
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Get the project ID from an environment variable
project_id = os.environ.get('GCLOUD_PROJECT')

# Get the Storage Bucket name from an environment variable
bucket_name = os.environ.get('STORAGE_BUCKET')

if not project_id:
    # Exit if the project ID is not set, but not in test mode
    if os.environ.get("FLASK_ENV") != "testing":
        sys.exit("The GCLOUD_PROJECT environment variable is not set. Please set it to your Firebase project ID.")

if not bucket_name:
    # Exit if the bucket name is not set, but not in test mode
    if os.environ.get("FLASK_ENV") != "testing":
        sys.exit("The STORAGE_BUCKET environment variable is not set. Please create a .env file and set it.")

# Initialize the Firebase Admin SDK, if not already done.
if not firebase_admin._apps:
    firebase_admin.initialize_app(options={
        'storageBucket': bucket_name
    })

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# --- Authentication Decorators ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # In a test environment, we can bypass the real token check
        if app.config.get('TESTING'):
            # You can set a mock user in your tests for specific scenarios
            g.user = getattr(g, '_user_mock', None)
            if g.user:
                return f(*args, **kwargs)
        
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization header missing"}), 401
        
        try:
            id_token = auth_header.split(' ').pop()
            decoded_token = auth.verify_id_token(id_token)
            g.user = decoded_token
        except Exception as e:
            return jsonify({"error": "Invalid token", "details": str(e)}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user or not g.user.get('admin'):
            return jsonify({"error": "Admin privileges required"}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- Agent Instances ---
expense_agent = ExpenseAgent()
doc_mgmt_agent = DocMgmtAgent(bucket_name)
email_agent = EmailAgent()
policy_rag = PolicyRAG()
orchestrator = OrchestratorAgent(expense_agent, doc_mgmt_agent, email_agent, policy_rag)

# --- Routes ---
@app.route("/")
def hello_world():
  """Example Hello World route."""
  name = os.environ.get("NAME", "World")
  return f"Hello {name}!"

@app.route("/expenses", methods=["POST"])
@login_required
def create_expense():
    """Creates a new expense and uploads the invoice with rollback."""
    if 'invoice' not in request.files:
        return jsonify({"error": "No invoice file provided."}), 400
    
    position = request.form.get('position')
    if not position:
        return jsonify({"error": "Position is a required field."}), 400

    file = request.files['invoice']
    employee_name = g.user.get('name') or g.user.get('email')

    # Step 1: Upload the document
    upload_result = doc_mgmt_agent.upload_document(file)
    if upload_result.get("error"):
        return jsonify({"error": upload_result["error"]}), 500

    file_path = upload_result.get("file_path")

    # Step 2: Try to create the expense record in the database
    try:
        expense_data = {
            "user_id": g.user['uid'],
            "employee_name": employee_name,
            "employee_email": g.user.get('email'),
            "position": position,
            "submission_time": datetime.utcnow(),
            "invoice_url": upload_result.get("public_url"),
            "status": "pending"
        }

        result = expense_agent.create_expense(expense_data)
        if result.get("error"):
            # If database write fails, roll back the file upload
            doc_mgmt_agent.delete_document(file_path)
            return jsonify({"error": "Database error, file upload rolled back.", "details": result.get("error")}), 500

        return jsonify({"success": f"Expense created successfully for {employee_name}"}), 201

    except Exception as e:
        # Catch any other unexpected errors and roll back
        doc_mgmt_agent.delete_document(file_path)
        return jsonify({"error": "An unexpected error occurred, rolling back operation.", "details": str(e)}), 500

@app.route("/expenses", methods=["GET"])
@login_required
def list_expenses():
    """Lists expenses. Admins see all, users see their own."""
    is_admin = g.user.get('admin', False)
    user_id = g.user['uid']
    
    expenses = expense_agent.list_expenses(is_admin=is_admin, user_id=user_id)
    if isinstance(expenses, dict) and "error" in expenses:
        return jsonify({"error": expenses["error"]}), 500
    return jsonify(expenses), 200

@app.route("/expenses/<expense_id>", methods=["PUT"])
@login_required
@admin_required
def update_expense(expense_id):
    """Updates the status of an expense and sends an email notification."""
    status = request.json.get('status')
    if not status:
        return jsonify({"error": "Status is required."}), 400

    # Get the expense to find the user's ID
    expense = expense_agent.get_expense(expense_id)
    if not expense:
        return jsonify({"error": "Expense not found."}), 404

    # Update the expense status
    result = expense_agent.update_expense_status(expense_id, status)
    if result.get("error"):
        return jsonify({"error": result.get("error")}), 500
    
    # Get the user's email and send a notification
    try:
        user = auth.get_user(expense['user_id'])
        subject = f"Your expense request has been {status}."
        body = f"Your expense request for the invoice <a href=\"{expense['invoice_url']}\">here</a> has been {status}."
        email_result = email_agent.send_email(user.email, subject, body)
        return jsonify({"success": f"Expense status updated. {email_result}"}), 200
    except Exception as e:
        return jsonify({"error": f"Expense status updated, but failed to send email: {e}"}), 500
