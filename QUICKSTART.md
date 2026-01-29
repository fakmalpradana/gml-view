# Quick Deployment Guide

## 🎯 One-Command Deployment

```bash
./deploy.sh
```

This script will:
1. ✅ Set project to `citygml-view`
2. ✅ Enable required APIs
3. ✅ Create service account
4. ✅ Grant permissions
5. ✅ Generate key (~gcp-key.json)
6. ✅ Build Docker image
7. ✅ Push to Google Container Registry
8. ✅ Deploy to Cloud Run
9. ✅ Show service URL

---

## 📋 Before Running

Make sure you're logged in:
```bash
gcloud auth login
gcloud config list  # Verify account
```

---

## 🚀 Deploy Now

```bash
# Make executable (already done)
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

---

## 🔑 After Deployment

1. **Copy service account key**:
   ```bash
   cat ~/gcp-key.json
   ```

2. **Add to GitHub Secrets**:
   - Go to: `https://github.com/YOUR_USERNAME/gml-view/settings/secrets/actions`
   - Add secret: `GCP_PROJECT_ID` = `citygml-view`
   - Add secret: `GCP_SA_KEY` = (paste entire JSON from above)

3. **Push to GitHub**:
   ```bash
   git commit -m "Add GCP deployment"
   git push origin main
   ```

4. **Auto-deploy is active!** Every push to main will deploy.

---

## 🌐 Access Your App

After deployment completes, the script will show your service URL:
```
https://citygml-viewer-xxx-uc.a.run.app
```

Or get it manually:
```bash
gcloud run services describe citygml-viewer --region us-central1 --format 'value(status.url)'
```

---

## 📊 Monitor

```bash
# View logs
gcloud run services logs tail citygml-viewer --region us-central1

# Check status
gcloud run services describe citygml-viewer --region us-central1
```

---

## 💰 Estimated Cost

- **Free tier**: 2M requests/month
- **Beyond free**: ~$5-15/month
- **Total**: Usually $0-10/month for moderate use

---

## 🔄 Update Deployment

Just push to main:
```bash
git add .
git commit -m "feat: update something"
git push origin main
```

GitHub Actions will auto-deploy! 🚀
