class EmailOrganizer:
    def __init__(self, gmail_client):
        self.client = gmail_client

    def mark_as_read(self, msg_id):
        return self.client.modify_labels(msg_id, remove=["UNREAD"])

    def mark_as_important(self, msg_id):
        return self.client.modify_labels(msg_id, add=["IMPORTANT"])

    def move_to_label(self, msg_id, label_id):
        return self.client.modify_labels(msg_id, add=[label_id])

    def auto_sort(self, parsed_msg):
        """Define your filtering logic."""
        subject = parsed_msg["subject"] or ""
        sender = parsed_msg["from"] or ""

        if "invoice" in subject.lower():
            self.move_to_label(parsed_msg["id"], "INVOICES")

        if sender.endswith("@company.com"):
            self.mark_as_important(parsed_msg["id"])

    def apply_filters(self, message_id, filter_config):
        """Apply filtering rules to organize email"""
        if "label" in filter_config:
            label_name = filter_config["label"]
            # Assuming you have a method to get/create label ID
            return self.client.modify_labels(
                message_id, 
                add_labels=[label_name]
            )
