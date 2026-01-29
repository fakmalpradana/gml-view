# GCP Deployment Setup Guide

## 📋 Prerequisites

- Google Cloud Platform account
- GitHub account
- `gcloud` CLI installed locally
- Docker installed locally (for testing)

---

## 🚀 Quick Setup (5 Steps)

### Step 1: Create GCP Project

```bash
# Create project (replace with your project ID)
gcloud projects create citygml-viewer-prod --name="CityGML Viewer"

# Set as active project
gcloud config set project citygml-viewer-prod

# Enable billing (required for Cloud Run)
# Go to: https://console.cloud.google.com/billing
```

### Step 2: Enable APIs

```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  containerregistry.googleapis.com
```

### Step 3: Create Service Account

```bash
# Create service account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions CI/CD"

# Grant permissions
gcloud projects add-iam-policy-binding citygml-viewer-prod \
  --member="serviceAccount:github-actions@citygml-viewer-prod.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding citygml-viewer-prod \
  --member="serviceAccount:github-actions@citygml-viewer-prod.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding citygml-viewer-prod \
  --member="serviceAccount:github-actions@citygml-viewer-prod.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Generate key
gcloud iam service-accounts keys create ~/gcp-key.json \
  --iam-account=github-actions@citygml-viewer-prod.iam.gserviceaccount.com

# Copy the entire content of ~/gcp-key.json for next step
cat ~/gcp-key.json
```

### Step 4: Add GitHub Secrets

Go to your GitHub repository:
1. Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add two secrets:

**Secret 1**: `GCP_PROJECT_ID`
```
citygml-viewer-prod
```

**Secret 2**: `GCP_SA_KEY`
```
(Paste entire content of ~/gcp-key.json here)
```

### Step 5: Deploy!

```bash
# Commit and push
git add .
git commit -m "Add GCP deployment with CI/CD"
git push origin main
```

✅ **Done!** GitHub Actions will automatically:
- Build Docker image
- Push to Google Container Registry
- Deploy to Cloud Run

Check deployment at: **Actions** tab in GitHub

---

## 🌐 Access Your App

After deployment completes:

```bash
# Get service URL
gcloud run services describe citygml-viewer \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)'
```

Or find it in:
- GitHub Actions logs (deployment summary)
- Cloud Run console: https://console.cloud.google.com/run

---

## 🔧 Configuration Options

### Custom Domain

```bash
# Add custom domain
gcloud run domain-mappings create \
  --service citygml-viewer \
  --domain yourdomain.com \
  --region us-central1
```

### Environment Variables

```bash
gcloud run services update citygml-viewer \
  --set-env-vars "FLASK_ENV=production,MAX_UPLOAD_SIZE=52428800" \
  --region us-central1
```

### Scale Configuration

```bash
# Set min/max instances
gcloud run services update citygml-viewer \
  --min-instances 1 \
  --max-instances 10 \
  --region us-central1
```

### Memory & CPU

```bash
gcloud run services update citygml-viewer \
  --memory 1Gi \
  --cpu 2 \
  --region us-central1
```

---

## 🧪 Test Locally with Docker

```bash
# Build
docker build -t citygml-viewer .

# Run
docker run -p 8080:8080 citygml-viewer

# Test
# Open http://localhost:8080/viewer.html
```

---

## 💰 Cost Estimates

**Free Tier** (first 2 million requests/month):
- Included: 180,000 vCPU-seconds
- Included: 360,000 GiB-seconds
- Included: 2M requests

**Beyond Free Tier**:
- ~$5-15/month for moderate traffic
- $1-3/month for Container Registry storage

**Total**: ~$0-18/month

---

## 📊 Monitoring

### View Logs

```bash
# Stream logs
gcloud run services logs tail citygml-viewer --region us-central1

# Or visit: https://console.cloud.google.com/logs
```

### Metrics

Visit Cloud Run console to see:
- Request count
- Response latency  
- Memory usage
- CPU utilization
- Error rates

---

## 🔒 Security

### Set up CORS properly

Update `server.py`:
```python
# Production CORS
CORS(app, origins=[
    "https://yourdomain.com",
    "https://citygml-viewer-*.run.app"
])
```

### Add Authentication (Optional)

For private deployments:
```bash
# Remove --allow-unauthenticated
gcloud run services update citygml-viewer \
  --no-allow-unauthenticated \
  --region us-central1
```

---

## 🐛 Troubleshooting

### Deployment Failed

Check GitHub Actions logs:
- Go to **Actions** tab
- Click on failed workflow
- Check error messages

### Service Not Responding

```bash
# Check service status
gcloud run services describe citygml-viewer \
  --region us-central1

# View recent logs
gcloud run services logs read citygml-viewer \
  --region us-central1 \
  --limit 50
```

### Common Issues

1. **Port mismatch**: Ensure Dockerfile EXPOSE matches Cloud Run PORT
2. **Dependencies**: Check requirements.txt includes all packages
3. **Memory**: Increase if getting OOM errors
4. **Timeout**: Increase for large file conversions

---

## 🔄 Update Deployment

Just push to main branch:
```bash
git add .
git commit -m "Update feature"
git push origin main
```

GitHub Actions will auto-deploy! 🚀

---

## 📚 Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [GitHub Actions](https://docs.github.com/en/actions)
- [gcloud CLI Reference](https://cloud.google.com/sdk/gcloud/reference)
