#!/bin/bash

# Update OPENAI_API_KEY secret in Google Cloud Secret Manager
# Run this from the backend directory: ./update-secret.sh

set -e

PROJECT_ID="expensense-8110a"
SECRET_NAME="OPENAI_API_KEY"

echo "🔐 Updating $SECRET_NAME in Secret Manager..."

# Get API key from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY not found in .env file"
    exit 1
fi

# Add new version to the secret
echo -n "$OPENAI_API_KEY" | gcloud secrets versions add $SECRET_NAME \
    --data-file=- \
    --project=$PROJECT_ID

echo "✅ Secret updated successfully!"
echo ""
echo "To deploy with the new secret, run:"
echo "  ./deploy.sh"
