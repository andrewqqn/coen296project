# api.py
from flask import Blueprint, request, jsonify, g
from functools import wraps
from firebase_admin import auth
from datetime import datetime

from src.agents import OrchestratorAgent, ExpenseAgent, DocMgmtAgent, EmailAgent, PolicyRAG

api_blueprint = Blueprint("api", __name__)

import os
bucket_name = os.environ.get("STORAGE_BUCKET", "")
expense_agent = ExpenseAgent()
doc_mgmt_agent = DocMgmtAgent(bucket_name)
email_agent = EmailAgent()
policy_rag = PolicyRAG()
orchestrator = OrchestratorAgent(expense_agent, doc_mgmt_agent, email_agent, policy_rag)

# --- Authentication Decorators ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authorization header missing"}), 401

        try:
            id_token = auth_header.split(" ").pop()
            decoded_token = auth.verify_id_token(id_token)
            g.user = decoded_token
        except Exception as e:
            return jsonify({"error": "Invalid token", "details": str(e)}), 401

        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user.get("admin"):
            return jsonify({"error": "Admin privileges required"}), 403
        return f(*args, **kwargs)
    return decorated_function


# --- Routes ---
@api_blueprint.route("/expenses", methods=["POST"])
@login_required
def create_expense():
    """Creates a new expense and uploads the invoice."""
    if "invoice" not in request.files:
        return jsonify({"error": "No invoice file provided."}), 400

    position = request.form.get("position")
    if not position:
        return jsonify({"error": "Position is a required field."}), 400

    file = request.files["invoice"]
    employee_name = g.user.get("name") or g.user.get("email")

    file_url = doc_mgmt_agent.upload_document(file)
    if "Error" in file_url or "No file" in file_url:
        return jsonify({"error": file_url}), 500

    expense_data = {
        "user_id": g.user["uid"],
        "employee_name": employee_name,
        "employee_email": g.user.get("email"),
        "position": position,
        "submission_time": datetime.utcnow(),
        "invoice_url": file_url,
        "status": "pending",
    }

    result = expense_agent.create_expense(expense_data)
    if "Error" in result:
        return jsonify({"error": result}), 500

    return jsonify({"success": f"Expense created successfully for {employee_name}"}), 201


@api_blueprint.route("/expenses", methods=["GET"])
@login_required
def list_expenses():
    """Lists expenses. Admins see all, users see their own."""
    is_admin = g.user.get("admin", False)
    user_id = g.user["uid"]

    expenses = expense_agent.list_expenses(is_admin=is_admin, user_id=user_id)
    if isinstance(expenses, str) and "Error" in expenses:
        return jsonify({"error": expenses}), 500
    return jsonify(expenses), 200


@api_blueprint.route("/expenses/<expense_id>", methods=["PUT"])
@login_required
@admin_required
def update_expense(expense_id):
    """Updates the status of an expense and sends an email notification."""
    status = request.json.get("status")
    if not status:
        return jsonify({"error": "Status is required."}), 400

    expense = expense_agent.get_expense(expense_id)
    if not expense:
        return jsonify({"error": "Expense not found."}), 404

    result = expense_agent.update_expense_status(expense_id, status)
    if "Error" in result:
        return jsonify({"error": result}), 500

    try:
        user = auth.get_user(expense["user_id"])
        subject = f"Your expense request has been {status}."
        body = f"Your expense request for the invoice <a href='{expense['invoice_url']}'>here</a> has been {status}."
        email_result = email_agent.send_email(user.email, subject, body)
        return jsonify({"success": f"Expense status updated. {email_result}"}), 200
    except Exception as e:
        return jsonify({"error": f"Expense status updated, but failed to send email: {e}"}), 500
