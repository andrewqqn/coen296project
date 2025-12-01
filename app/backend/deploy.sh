#!/bin/bash

# Deploy backend to Google Cloud Run
# Run this from the backend directory: ./deploy.sh

set -e

echo "🚀 Deploying Expensense Backend to Cloud Run..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Install it first:"
    echo "   brew install google-cloud-sdk"
    exit 1
fi

# Set project
PROJECT_ID="expensense-8110a"
SERVICE_NAME="expensense-backend"
REGION="us-central1"

echo "📦 Project: $PROJECT_ID"
echo "📦 Service: $SERVICE_NAME"
echo "📦 Region: $REGION"

# Get OpenAI API key from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY not found in .env file"
    exit 1
fi

# Deploy with extended startup timeout
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --project $PROJECT_ID \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --cpu-boost \
  --no-cpu-throttling \
  --set-env-vars="PROJECT_ID=$PROJECT_ID,FIREBASE_PROJECT_ID=$PROJECT_ID,ENVIRONMENT=production,OPENAI_API_KEY=$OPENAI_API_KEY,STORAGE_BUCKET=${PROJECT_ID}.firebasestorage.app,USE_FIRlse"OR=faE_EMULATESTOR

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Get your service URL:"
echo "  gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)'"
