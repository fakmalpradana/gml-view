#!/bin/bash

#================================================================
# Complete GCP Deployment Script - CityGML Viewer with Storage
# Region: asia-southeast2 (Jakarta, Indonesia)
#================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="citygml-view"
SERVICE_NAME="citygml-viewer"
BUCKET_NAME="citygml-viewer-storage"
SA_NAME="citygml-viewer-sa"
REGION="asia-southeast2"  # Jakarta, Indonesia

echo -e "${GREEN}🚀 CityGML Viewer - Complete GCP Setup${NC}"
echo -e "${GREEN}=======================================${NC}"
echo ""
echo "Project: $PROJECT_ID"
echo "Region: $REGION (Jakarta, Indonesia)"
echo "Service: $SERVICE_NAME"
echo "Bucket: gs://$BUCKET_NAME"
echo ""

# Step 1: Set Project
echo -e "${YELLOW}📌 Step 1: Setting project...${NC}"
gcloud config set project $PROJECT_ID
echo -e "${GREEN}✓ Project set${NC}"
echo ""

# Step 2: Enable APIs
echo -e "${YELLOW}📌 Step 2: Enabling required APIs...${NC}"
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  storage.googleapis.com \
  containerregistry.googleapis.com
echo -e "${GREEN}✓ APIs enabled${NC}"
echo ""

# Step 3: Create Storage Bucket
echo -e "${YELLOW}📌 Step 3: Creating Cloud Storage bucket...${NC}"
if gsutil ls gs://$BUCKET_NAME 2>/dev/null; then
    echo "Bucket already exists"
else
    gsutil mb -l $REGION gs://$BUCKET_NAME
    echo -e "${GREEN}✓ Bucket created${NC}"
fi

# Set bucket lifecycle (delete files older than 7 days)
cat > /tmp/bucket-lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 7}
      }
    ]
  }
}
EOF

gsutil lifecycle set /tmp/bucket-lifecycle.json gs://$BUCKET_NAME
echo -e "${GREEN}✓ Lifecycle policy set (delete after 7 days)${NC}"

# Set CORS for bucket
cat > /tmp/cors.json <<EOF
[
  {
    "origin": ["*"],
    "method": ["GET", "HEAD", "DELETE"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF

gsutil cors set /tmp/cors.json gs://$BUCKET_NAME
echo -e "${GREEN}✓ CORS configured${NC}"
echo ""

# Step 4: Create Service Account
echo -e "${YELLOW}📌 Step 4: Creating service account...${NC}"
if gcloud iam service-accounts describe $SA_NAME@$PROJECT_ID.iam.gserviceaccount.com 2>/dev/null; then
    echo "Service account already exists"
else
    gcloud iam service-accounts create $SA_NAME \
      --display-name="$SERVICE_NAME Service Account" \
      --project=$PROJECT_ID
    echo -e "${GREEN}✓ Service account created${NC}"
fi
echo ""

# Step 5: Grant Permissions
echo -e "${YELLOW}📌 Step 5: Granting permissions...${NC}"

# Grant Storage Object Admin access to bucket
gsutil iam ch serviceAccount:$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com:objectAdmin \
  gs://$BUCKET_NAME

# Grant Cloud Run Invoker
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --condition=None

echo -e "${GREEN}✓ Permissions granted${NC}"
echo ""

# Step 6: Build and Deploy to Cloud Run
echo -e "${YELLOW}📌 Step 6: Building and deploying to Cloud Run...${NC}"
echo "This may take 5-10 minutes..."
echo ""

gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --service-account $SA_NAME@$PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars GCS_BUCKET=$BUCKET_NAME,REGION=$REGION \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --port 8080 \
  --quiet

echo ""
echo -e "${GREEN}✓ Deployment complete${NC}"
echo ""

# Step 7: Get Service URL
echo -e "${YELLOW}📌 Step 7: Getting service URL...${NC}"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format 'value(status.url)')

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ DEPLOYMENT SUCCESSFUL!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Service URL:${NC} $SERVICE_URL"
echo -e "${YELLOW}Viewer:${NC} $SERVICE_URL/viewer.html"
echo -e "${YELLOW}API Docs:${NC} $SERVICE_URL/api"
echo ""
echo -e "${YELLOW}Storage Bucket:${NC} gs://$BUCKET_NAME"
echo -e "${YELLOW}Region:${NC} $REGION (Jakarta)"
echo ""
echo -e "${GREEN}🎉 Your CityGML Viewer is live!${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Visit $SERVICE_URL/viewer.html"
echo "2. Upload a test GML file"
echo "3. Check Cloud Storage: https://console.cloud.google.com/storage/browser/$BUCKET_NAME"
echo "4. Monitor logs: gcloud run services logs tail $SERVICE_NAME --region $REGION"
echo ""
echo -e "${YELLOW}Cost Estimate:${NC} ~\$0-15/month (with free tier)"
echo ""
