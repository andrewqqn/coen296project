import pytest
from unittest.mock import MagicMock
from email_agent.gmail.gmail_client import GmailClient
from googleapiclient.errors import HttpError


def test_get_authenticated_user_email():
    service = MagicMock()
    service.users().getProfile().execute.return_value = {"emailAddress": "test@example.com"}

    client = GmailClient(service)
    email = client.get_authenticated_user_email()

    assert email == "test@example.com"


def test_send_email_success():
    service = MagicMock()
    send = service.users.return_value.messages.return_value.send
    send.return_value.execute.return_value = {"id": "123"}

    client = GmailClient(service)
    result = client.send_email({"raw": "abc"})

    assert result["id"] == "123"
    send.assert_called_once()  # or assert_called_once_with(...)


def test_list_messages():
    service = MagicMock()
    service.users().messages().list().execute.return_value = {
        "messages": [{"id": "1"}, {"id": "2"}]
    }

    client = GmailClient(service)
    msgs = client.list_messages()

    assert len(msgs) == 2
    assert msgs[0]["id"] == "1"


def test_modify_labels_error_handling(caplog):
    service = MagicMock()
    service.users().messages().modify.side_effect = Exception("API failure")

    client = GmailClient(service)
    result = client.modify_labels("123", add_labels=["Label_1"])

    # Should return None instead of throwing
    assert result is None
