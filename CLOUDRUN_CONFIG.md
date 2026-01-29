# Cloud Run Console Configuration Guide

## 🎯 You've connected GitHub - Now configure:

### 📋 Step-by-Step Configuration

---

## 1️⃣ Source (Already Done ✅)
- Repository: `fakmalpradana/gml-view`
- Branch: `^main$` (trigger on main branch)

---

## 2️⃣ Build Configuration

### Build Type:
- ✅ **Dockerfile** (use existing Dockerfile)
- Location: `/Dockerfile` (root of repo)

### Buildpack (ignore this, using Dockerfile)

---

## 3️⃣ Service Settings

### Service Name:
```
citygml-viewer
```

### Region:
```
asia-southeast2 (Jakarta)
```

---

## 4️⃣ Container Settings

### **Port**:
```
8080
```
⚠️ **CRITICAL**: Must be 8080 (matches Dockerfile)

### Container Command:
```
(leave empty - uses Dockerfile CMD)
```

### Container Arguments:
```
(leave empty)
```

---

## 5️⃣ Resources (Capacity)

### **Memory**:
```
512 MiB
```
(Sufficient for Flask + file conversion)

### **CPU**:
```
1 vCPU
```

### **Request timeout**:
```
300 seconds
```
(5 minutes - needed for large file conversions)

### **Maximum concurrent requests per instance**:
```
80
```
(default is fine)

---

## 6️⃣ Autoscaling

### **Minimum number of instances**:
```
0
```
(Scale to zero to save cost)

### **Maximum number of instances**:
```
10
```
(Adjust based on expected traffic)

---

## 7️⃣ Security

### Authentication:
- ✅ **Allow unauthenticated invocations**
  (So anyone can access your viewer)

### Service Account:
```
Default compute service account
```

---

## 8️⃣ Connections (Networking)

### Ingress:
```
All
```
(Allow all traffic)

### Egress:
```
All
```

---

## 9️⃣ Environment Variables (Optional)

Click **"ADD VARIABLE"** if needed:

```
FLASK_ENV = production
PORT = 8080
```

⚠️ PORT is already set by Cloud Run, but explicit is fine.

---

## 🔟 Volumes & Cloud SQL (Skip)

Leave empty unless you need persistent storage.

---

## ✅ Final Review

Before deploying, verify:

- [x] Region: **asia-southeast2** (Jakarta)
- [x] Port: **8080**
- [x] Memory: **512 MiB**
- [x] CPU: **1**
- [x] Timeout: **300 seconds**
- [x] Min instances: **0**
- [x] Max instances: **10**
- [x] Allow unauthenticated: **YES**

---

## 🚀 Deploy!

1. Click **"CREATE"** or **"DEPLOY"**
2. Wait 5-10 minutes for build
3. Get your URL: `https://citygml-viewer-xxx-asia-southeast2.run.app`

---

## 📊 After Deployment

### Test Your App:
1. Visit the URL
2. Go to `/viewer.html`
3. Upload a test GML file
4. Check `/api` for API docs

### Monitor:
- **Logs**: Cloud Run → citygml-viewer → Logs tab
- **Metrics**: Cloud Run → citygml-viewer → Metrics tab

---

## 🔄 Auto-Deploy

Now every push to `main` branch will:
1. Trigger Cloud Build
2. Build Docker image
3. Deploy to Cloud Run
4. Update your service automatically

✅ **No manual deployment needed!**

---

## 🐛 Troubleshooting

### Build Fails:
- Check "Build" tab in Cloud Run console
- Look for Docker errors
- Verify Dockerfile is in root

### Service Crashes:
- Check logs for errors
- Verify PORT=8080 in container
- Check memory isn't exceeded

### Can't Access:
- Verify "Allow unauthenticated" is enabled
- Check firewall rules
- Verify region is correct

---

## 💰 Cost Estimate

With these settings:
- **Free tier**: 2M requests/month
- **Min instances = 0**: Pay only when used
- **Expected**: $0-10/month for moderate traffic

---

## 📝 Quick Settings Summary

Copy this for reference:

```yaml
Service: citygml-viewer
Region: asia-southeast2
Port: 8080
Memory: 512 MiB
CPU: 1
Timeout: 300s
Min Instances: 0
Max Instances: 10
Auth: unauthenticated
```
