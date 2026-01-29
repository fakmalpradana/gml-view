#!/bin/bash

# GCP Deployment Script for CityGML Viewer
# Project: citygml-view

set -e  # Exit on error

echo "🚀 Starting GCP Deployment..."
echo "================================"

# Configuration
PROJECT_ID="citygml-view"
SERVICE_NAME="citygml-viewer"
REGION="asia-southeast2"  # Jakarta, Indonesia (closest to Indonesia)
SA_NAME="github-actions"

# Step 1: Set active project
echo "📌 Step 1: Setting project to $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Step 2: Enable required APIs
echo "📌 Step 2: Enabling APIs..."
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  containerregistry.googleapis.com

# Step 3: Create service account
echo "📌 Step 3: Creating service account..."
gcloud iam service-accounts create $SA_NAME \
  --display-name="GitHub Actions CI/CD" \
  --project=$PROJECT_ID || echo "Service account already exists"

# Step 4: Grant permissions to service account
echo "📌 Step 4: Granting permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Step 5: Generate service account key
echo "📌 Step 5: Generating service account key..."
gcloud iam service-accounts keys create ~/gcp-key.json \
  --iam-account=$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com

echo "✅ Service account key saved to ~/gcp-key.json"
echo ""
echo "⚠️  IMPORTANT: Copy this key to GitHub Secrets as GCP_SA_KEY"
echo "   Visit: https://github.com/<your-username>/<your-repo>/settings/secrets/actions"
echo ""

# Step 6: Configure Docker for GCR
echo "📌 Step 6: Configuring Docker..."
gcloud auth configure-docker

# Step 7: Build Docker image
echo "📌 Step 7: Building Docker image..."
docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME:latest .

# Step 8: Push to Container Registry
echo "📌 Step 8: Pushing to Google Container Registry..."
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:latest

# Step 9: Deploy to Cloud Run
echo "📌 Step 9: Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --port 8080 \
  --quiet

# Step 10: Get service URL
echo "📌 Step 10: Getting service URL..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --format 'value(status.url)')

echo ""
echo "================================"
echo "✅ Deployment Complete!"
echo "================================"
echo ""
echo "📍 Service URL: $SERVICE_URL"
echo "📍 Region: $REGION"
echo "📍 Image: gcr.io/$PROJECT_ID/$SERVICE_NAME:latest"
echo ""
echo "🔑 Next Steps:"
echo "1. Add GitHub Secrets:"
echo "   - GCP_PROJECT_ID: $PROJECT_ID"
echo "   - GCP_SA_KEY: (content of ~/gcp-key.json)"
echo ""
echo "2. Push to GitHub main branch to trigger CI/CD"
echo ""
echo "3. View logs: gcloud run services logs tail $SERVICE_NAME --region $REGION"
echo ""
