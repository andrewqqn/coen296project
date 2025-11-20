from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import json

# Generate a real RSA key
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)

# Serialize to PEM format
pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption()
).decode('utf-8')

# Create the service account JSON
service_account = {
    'type': 'service_account',
    'project_id': 'expensense-8110a',
    'private_key_id': 'fake-key-id-for-emulator',
    'private_key': pem,
    'client_email': 'firebase-adminsdk@expensense-8110a.iam.gserviceaccount.com',
    'client_id': '123456789',
    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
    'token_uri': 'https://oauth2.googleapis.com/token',
    'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs'
}

import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, 'emulator-credentials.json')

with open(output_path, 'w') as f:
    json.dump(service_account, f, indent=2)

print(f'Mock credentials generated successfully at {output_path}')
