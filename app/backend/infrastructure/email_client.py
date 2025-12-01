def send_email(to, subject, body):
    print(f"Sending email to {to} ...")
    return {"status": "sent", "to": to}
