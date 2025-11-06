import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set dummy environment variables before importing the app
# This is crucial for the app to initialize without errors.
os.environ['GCLOUD_PROJECT'] = 'test-project'
os.environ['STORAGE_BUCKET'] = 'test-bucket'

from main import app

# --- Mock Data ---
FAKE_USER = {
    "uid": "test-user-id-123",
    "name": "Test User",
    "email": "test@example.com",
    "admin": False
}

FAKE_ADMIN = {
    "uid": "test-admin-id-456",
    "name": "Admin User",
    "email": "admin@example.com",
    "admin": True
}

# --- Pytest Fixtures ---

@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# --- Test Cases ---

def test_auth_required(client):
    """
    GIVEN a Flask application
    WHEN a protected endpoint is accessed without a token
    THEN check that a 401 Unauthorized response is returned
    """
    response = client.get("/expenses")
    assert response.status_code == 401
    assert "Authorization header missing" in response.json['error']

@patch('main.auth.verify_id_token')
@patch('main.expense_agent.list_expenses')
def test_get_expenses_as_user(mock_list_expenses, mock_verify_token, client):
    """
    GIVEN a regular user
    WHEN they request the /expenses endpoint
    THEN check that the expense_agent's list_expenses method is called correctly for a non-admin
    """
    mock_verify_token.return_value = FAKE_USER
    mock_list_expenses.return_value = [{"id": "exp1", "employee_name": "Test User"}]
    
    headers = {"Authorization": "Bearer fake-token"}
    response = client.get("/expenses", headers=headers)
    
    assert response.status_code == 200
    mock_list_expenses.assert_called_once_with(is_admin=False, user_id=FAKE_USER['uid'])

@patch('main.auth.verify_id_token')
@patch('main.expense_agent.list_expenses')
def test_get_expenses_as_admin(mock_list_expenses, mock_verify_token, client):
    """
    GIVEN an admin user
    WHEN they request the /expenses endpoint
    THEN check that the expense_agent's list_expenses method is called correctly for an admin
    """
    mock_verify_token.return_value = FAKE_ADMIN
    mock_list_expenses.return_value = [{"id": "exp1"}, {"id": "exp2"}]
    
    headers = {"Authorization": "Bearer fake-token"}
    response = client.get("/expenses", headers=headers)
    
    assert response.status_code == 200
    mock_list_expenses.assert_called_once_with(is_admin=True, user_id=FAKE_ADMIN['uid'])

@patch('main.auth.verify_id_token')
@patch('main.doc_mgmt_agent.upload_document')
@patch('main.expense_agent.create_expense')
def test_create_expense_success(mock_create_expense, mock_upload, mock_verify_token, client):
    """
    GIVEN a logged-in user
    WHEN they submit a new expense with a file successfully
    THEN check that the document is uploaded and the expense is created
    """
    mock_verify_token.return_value = FAKE_USER
    mock_upload.return_value = {"public_url": "http://fake-url.com/invoice.pdf", "file_path": "invoices/test.txt"}
    mock_create_expense.return_value = {"success": True}

    headers = {"Authorization": "Bearer fake-token"}
    data = {
        'position': 'Software Engineer',
        'invoice': (open(__file__, 'rb'), 'test.txt') # Simple fake file upload
    }
    
    response = client.post("/expenses", headers=headers, data=data, content_type='multipart/form-data')
    
    assert response.status_code == 201
    mock_upload.assert_called_once()
    mock_create_expense.assert_called_once()
    assert "Expense created successfully" in response.json['success']

@patch('main.auth.verify_id_token')
@patch('main.doc_mgmt_agent.delete_document')
@patch('main.doc_mgmt_agent.upload_document')
@patch('main.expense_agent.create_expense')
def test_create_expense_rollback_on_db_failure(mock_create_expense, mock_upload, mock_delete, mock_verify_token, client):
    """
    GIVEN a logged-in user
    WHEN the database write fails after a file upload
    THEN check that the uploaded file is deleted (rolled back)
    """
    mock_verify_token.return_value = FAKE_USER
    mock_upload.return_value = {"public_url": "http://fake-url.com/invoice.pdf", "file_path": "invoices/test.txt"}
    mock_create_expense.return_value = {"error": "Simulated database failure"}

    headers = {"Authorization": "Bearer fake-token"}
    data = {
        'position': 'Software Engineer',
        'invoice': (open(__file__, 'rb'), 'test.txt')
    }
    
    response = client.post("/expenses", headers=headers, data=data, content_type='multipart/form-data')
    
    assert response.status_code == 500
    mock_upload.assert_called_once()
    mock_create_expense.assert_called_once()
    mock_delete.assert_called_once_with("invoices/test.txt")
    assert "Database error, file upload rolled back" in response.json['error']

@patch('main.auth.verify_id_token')
def test_update_expense_by_non_admin(mock_verify_token, client):
    """
    GIVEN a regular user
    WHEN they attempt to update an expense status
    THEN check that a 403 Forbidden response is returned
    """
    mock_verify_token.return_value = FAKE_USER # User is NOT an admin
    
    headers = {"Authorization": "Bearer fake-token"}
    data = {'status': 'approved'}
    
    response = client.put("/expenses/some-expense-id", headers=headers, json=data)
    
    assert response.status_code == 403
    assert "Admin privileges required" in response.json['error']

@patch('main.auth.verify_id_token')
@patch('main.expense_agent.get_expense')
@patch('main.expense_agent.update_expense_status')
@patch('main.email_agent.send_email')
@patch('main.auth.get_user')
def test_update_expense_by_admin(mock_get_auth_user, mock_send_email, mock_update_status, mock_get_expense, mock_verify_token, client):
    """
    GIVEN an admin user
    WHEN they update an expense status
    THEN check that the status is updated and an email is sent
    """
    mock_verify_token.return_value = FAKE_ADMIN # User IS an admin
    mock_get_expense.return_value = {'user_id': 'test-user-id-123', 'invoice_url': 'http://fake.com/inv.pdf'}
    mock_update_status.return_value = {"success": True}
    
    # Mock the return of auth.get_user to have an email attribute
    mock_user_record = MagicMock()
    mock_user_record.email = 'user@example.com'
    mock_get_auth_user.return_value = mock_user_record

    headers = {"Authorization": "Bearer fake-token"}
    data = {'status': 'approved'}
    
    response = client.put("/expenses/some-expense-id", headers=headers, json=data)
    
    assert response.status_code == 200
    mock_update_status.assert_called_once_with('some-expense-id', 'approved')
    mock_send_email.assert_called_once()
    assert "Expense status updated" in response.json['success']
