from unittest.mock import MagicMock
from email_agent.services.email_organizer import EmailOrganizer


def test_apply_filters_move_to_label():
    client = MagicMock()
    organizer = EmailOrganizer(client)

    organizer.apply_filters("123", {"label": "Expenses"})

    client.modify_labels.assert_called_once()
