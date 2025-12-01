#!/bin/bash

# Setup Gmail secrets in Google Cloud Secret Manager
# Run this once before deploying: ./setup-gmail-secrets.sh

set -e

PROJECT_ID="expensense-8110a"

echo "🔐 Setting up Gmail secrets in Google Cloud Secret Manager..."
echo "📦 Project: $PROJECT_ID"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Install it first:"
    echo "   brew install google-cloud-sdk"
    exit 1
fi

# Check if credential files exist
if [ ! -f "gmail_oauth_credentials.json" ]; then
    echo "❌ gmail_oauth_credentials.json not found in current directory"
    exit 1
fi

if [ ! -f "gmail_token.json" ]; then
    echo "❌ gmail_token.json not found in current directory"
    exit 1
fi

echo "📄 Found credential files"
echo ""

# Create or update GMAIL_CREDENTIALS_FILE secret
echo "🔐 Creating/updating GMAIL_CREDENTIALS_FILE secret..."
if gcloud secrets describe GMAIL_CREDENTIALS_FILE --project=$PROJECT_ID &> /dev/null; then
    echo "   Secret exists, adding new version..."
    gcloud secrets versions add GMAIL_CREDENTIALS_FILE \
        --data-file=gmail_oauth_credentials.json \
        --project=$PROJECT_ID
else
    echo "   Creating new secret..."
    gcloud secrets create GMAIL_CREDENTIALS_FILE \
        --data-file=gmail_oauth_credentials.json \
        --project=$PROJECT_ID
fi

# Create or update GMAIL_TOKEN_FILE secret
echo "🔐 Creating/updating GMAIL_TOKEN_FILE secret..."
if gcloud secrets describe GMAIL_TOKEN_FILE --project=$PROJECT_ID &> /dev/null; then
    echo "   Secret exists, adding new version..."
    gcloud secrets versions add GMAIL_TOKEN_FILE \
        --data-file=gmail_token.json \
        --project=$PROJECT_ID
else
    echo "   Creating new secret..."
    gcloud secrets create GMAIL_TOKEN_FILE \
        --data-file=gmail_token.json \
        --project=$PROJECT_ID
fi

echo ""
echo "✅ Secrets created successfully!"
echo ""
echo "📋 Next steps:"
echo "   1. Grant Cloud Run service account access to secrets:"
echo "      PROJECT_NUMBER=\$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')"
echo "      gcloud secrets add-iam-policy-binding GMAIL_CREDENTIALS_FILE \\"
echo "        --member=\"serviceAccount:\${PROJECT_NUMBER}-compute@developer.gserviceaccount.com\" \\"
echo "        --role=\"roles/secretmanager.secretAccessor\" \\"
echo "        --project=$PROJECT_ID"
echo ""
echo "      gcloud secrets add-iam-policy-binding GMAIL_TOKEN_FILE \\"
echo "        --member=\"serviceAccount:\${PROJECT_NUMBER}-compute@developer.gserviceaccount.com\" \\"
echo "        --role=\"roles/secretmanager.secretAccessor\" \\"
echo "        --project=$PROJECT_ID"
echo ""
echo "   2. Deploy your backend: ./deploy.sh"
