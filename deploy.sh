#!/bin/bash

# Google Cloud Deployment Script for Error Screen Fix Backend

echo "🚀 Deploying Error Screen Fix Backend to Google Cloud Run..."

# Set project
gcloud config set project error-fixer-23274

# Enable required APIs
echo "📋 Enabling required Google Cloud APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Deploy to Cloud Run
echo "🔧 Deploying to Cloud Run..."
gcloud run deploy error-screen-fix-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars="FLASK_ENV=production,PORT=8080"

echo "✅ Deployment complete!"
echo "📋 Your backend URL will be displayed above."
echo "🔧 Update the frontend API_BASE_URL with this URL and redeploy."

