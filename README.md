# 🌍 CityGML Viewer

A high-performance web-based viewer for CityGML files with automatic GLB conversion and interactive 3D visualization.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

- 🚀 **Fast GLB Conversion**: Converts CityGML to optimized GLB format (70-80% smaller files, 5-10x faster loading)
- 🎯 **Interactive 3D Viewer**: Built with Three.js for smooth 60 FPS performance
- 📊 **Metadata Extraction**: Automatic extraction of building attributes (height, storeys, descriptions)
- 🖱️ **Click Detection**: Select buildings to view detailed attributes
- 📋 **Object List**: Searchable sidebar with all buildings
- 🎨 **Color Coding**: Visual distinction by building elements (roof, wall, ground)
- 🔄 **Session Management**: Automatic cleanup of temporary files
- 📖 **API Documentation**: Interactive Swagger UI for API testing

---

## 🎬 Quick Start

```bash
# 1. Clone repository
git clone <repository-url>
cd gml-view

# 2. Setup (installs dependencies, creates directories)
./scripts/setup_server.sh

# 3. Start server
./scripts/start_server.sh

# 4. Open viewer
# Visit: http://localhost:8080/viewer.html
# API Docs: http://localhost:5001/api
```

---

## 📦 Installation

### Prerequisites

- **Python 3.8+**
- **pip** (Python package manager)
- **Modern web browser** with WebGL 2.0 support

### Setup Steps

1. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

Dependencies:
- `flask` - Web server
- `flask-cors` - CORS support
- `trimesh[easy]` - 3D geometry processing
- `pygltflib` - GLB file generation
- `lxml` - XML parsing

2. **Verify installation**:
```bash
python3 -c "import flask, trimesh, pygltflib, lxml; print('✅ All dependencies installed')"
```

3. **Create required directories**:
```bash
mkdir -p temp_models uploads
```

---

##  Architecture

```
┌──────────────┐
│   User       │
│   Browser    │
└──────┬───────┘
       │ Upload .gml
       ▼
┌──────────────────────────────────────┐
│  Flask Server (port 5001)            │
│  ┌────────────────────────────────┐  │
│  │  /upload → gml2glb.py          │  │
│  │  Converts CityGML to GLB       │  │
│  │  Extracts building metadata    │  │
│  └────────────────────────────────┘  │
│  ┌────────────────────────────────┐  │
│  │  /models/{id}/model.glb        │  │
│  │  /models/{id}/metadata.json    │  │
│  └────────────────────────────────┘  │
└───────────────┬──────────────────────┘
                ▼
         ┌─────────────┐
         │  viewer.html │
         │  Three.js    │
         │  GLTFLoader  │
         └─────────────┘
```

### Components

- **gml2glb.py**: CityGML → GLB converter with metadata extraction
- **server.py**: Flask API server for file upload and conversion
- **viewer.html**: Interactive 3D viewer (HTML structure)
- **static/css/viewer.css**: Viewer styles
- **static/js/viewer.js**: Viewer logic (Three.js, interactions)

---

## 🔧 Usage

### Starting the Server

**Option 1: Using script** (recommended):
```bash
./scripts/start_server.sh
```

**Option 2: Manual**:
```bash
python3 server.py
```

Server will start on `http://localhost:5001`

### Using the Viewer

1. **Open viewer**: Navigate to `http://localhost:8080/viewer.html`

2. **Upload CityGML file**:
   - Click "📁 Upload GML" button
   - Drag & drop `.gml` or `.xml` file
   - Or click "Browse Files" to select file
   - Wait for conversion and loading

3. **Navigate the 3D scene**:
   - **Rotate**: Left click + drag
   - **Pan**: Right click + drag  
   - **Zoom**: Mouse scroll wheel

4. **Interact with buildings**:
   - Click "📋 Object List" to see all buildings
   - Search for specific buildings
   - Click on building in list or 3D view to select
   - View attributes in bottom-right panel
   - Click "🎯 Fly To Object" to focus camera

5. **Unload model**:
   - Click "❌ Unload Model"
   - Automatically cleans up server files

---

## 📖 API Documentation

### Interactive Docs

Visit **http://localhost:5001/api** for interactive Swagger UI with "Try it out" functionality.

### Endpoints

#### 1. Upload & Convert CityGML

```bash
POST /upload
Content-Type: multipart/form-data

curl -X POST http://localhost:5001/upload \
  -F "file=@data/AT_30_A.gml"
```

**Response**:
```json
{
  "session_id": "uuid",
  "filename": "AT_30_A.gml",
  "files": {
    "glb": "/models/{id}/model.glb",
    "metadata": "/models/{id}/model_metadata.json"
  }
}
```

#### 2. Download GLB Model

```bash
GET /models/{session_id}/model.glb

curl -O http://localhost:5001/models/{id}/model.glb
```

#### 3. Download Metadata

```bash
GET /models/{session_id}/model_metadata.json

curl http://localhost:5001/models/{id}/model_metadata.json
```

#### 4. Cleanup Session

```bash
DELETE /cleanup/{session_id}

curl -X DELETE http://localhost:5001/cleanup/{id}
```

#### 5. List Active Sessions

```bash
GET /sessions

curl http://localhost:5001/sessions
```

#### 6. Cleanup All

```bash
DELETE /cleanup-all

curl -X DELETE http://localhost:5001/cleanup-all
```

### Python Client Example

```python
import requests

# Upload CityGML
with open('data/AT_30_A.gml', 'rb') as f:
    response = requests.post(
        'http://localhost:5001/upload',
        files={'file': f}
    )

result = response.json()
session_id = result['session_id']

# Download GLB
glb_url = f"http://localhost:5001{result['files']['glb']}"
glb_data = requests.get(glb_url).content

with open('output.glb', 'wb') as f:
    f.write(glb_data)

# Get metadata
metadata_url = f"http://localhost:5001{result['files']['metadata']}"
metadata = requests.get(metadata_url).json()

print(f"Total buildings: {metadata['total_objects']}")

# Cleanup
requests.delete(f'http://localhost:5001/cleanup/{session_id}')
```

### JavaScript Client Example

```javascript
// Upload file
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:5001/upload', {
    method: 'POST',
    body: formData
});

const result = await response.json();

// Load GLB with Three.js
const loader = new GLTFLoader();
loader.load(
    `http://localhost:5001${result.files.glb}`,
    (gltf) => scene.add(gltf.scene)
);

// Cleanup when done
await fetch(`http://localhost:5001/cleanup/${result.session_id}`, {
    method: 'DELETE'
});
```

---

## 🗂️ Project Structure

```
gml-view/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
│
├── gml2glb.py                   # CityGML → GLB converter
├── server.py                    # Flask API server
├── viewer.html                  # Viewer HTML structure
│
├── docs/
│   ├── openapi.yaml             # API specification
│   └── swagger_ui.html          # API docs UI
│
├── scripts/
│   ├── start_server.sh          # Start server script
│   └── setup_server.sh          # Setup script
│
├── static/
│   ├── css/
│   │   └── viewer.css           # Viewer styles (497 lines)
│   └── js/
│       └── viewer.js            # Viewer logic (810 lines)
│
└── [Runtime directories]
    ├── data/                    # Sample CityGML files
    ├── temp_models/             # Converted GLB files
    └── uploads/                 # Uploaded GML files
```

---

## 🎯 Viewer Controls

### Mouse Controls
- **Left Click + Drag**: Rotate camera around model
- **Right Click + Drag**: Pan camera (move view)
- **Scroll Wheel**: Zoom in/out

### Keyboard Shortcuts
- **Esc**: Close attribute panel or upload modal
- **Ctrl/Cmd + F**: Focus search box (when object list open)

### UI Buttons
- **📁 Upload GML**: Open file upload dialog
- **❌ Unload Model**: Remove current model and cleanup files
- **📋 Object List**: Toggle searchable building list sidebar
- **🎯 Fly To Object**: Animate camera to selected building

---

## 🚀 Performance

### File Size Comparison

| Format | File Size | Load Time | Notes |
|--------|-----------|-----------|-------|
| **OBJ** | 8-10 MB | 3-5 sec | Text format, large |
| **GLB** | 2-3 MB | 0.5-1 sec | Binary, optimized ✅ |

**Improvement**: 70-80% smaller files, 5-10x faster loading

### Real Results

- **AT_30_A.gml** (460 buildings): 3.27 MB GLB
- **AU_16_A.gml** (50 buildings): 1.99 MB GLB
- Viewer runs at **60 FPS** with smooth interactions

---

## 🐛 Troubleshooting

### Server won't start

**Error**: `ModuleNotFoundError: No module named 'flask'`

**Solution**:
```bash
pip install -r requirements.txt
```

### Conversion fails

**Error**: `Conversion timeout`

**Solution**: Large files (>50MB) may timeout. Increase timeout in `server.py`:
```python
# Line ~150
result = subprocess.run(..., timeout=600)  # 10 minutes
```

### Viewer shows blank screen

**Possible causes**:
1. Server not running → Check `http://localhost:5001/health`
2. Browser cache → Hard refresh (Cmd+Shift+R or Ctrl+Shift+R)
3. WebGL not supported → Use Chrome, Firefox, or Edge

### Click detection not working

**Solution**: Ensure metadata JSON is loaded. Check browser console for errors.

### Port already in use

**Error**: `Address already in use`

**Solution**:
```bash
# Find process using port 5001
lsof -i :5001

# Kill process
kill -9 <PID>

# Or change port in server.py (line ~280)
app.run(host='0.0.0.0', port=5002, debug=True)
```

---

## 📝 Development

### Adding a New Feature

1 . Code changes in appropriate files:
   - Server logic → `server.py`
   - Converter → `gml2glb.py`
   - Viewer logic → `static/js/viewer.js`
   - Viewer styles → `static/css/viewer.css`

2. Test locally
3. Update API docs if needed → `docs/openapi.yaml`
4. Update README with new features

### Running Tests

```bash
# Test GLB conversion
python3 gml2glb.py data/AT_30_A.gml test.glb
ls -lh test.glb test_metadata.json

# Test server health
curl http://localhost:5001/health

# Test full upload workflow
curl -X POST http://localhost:5001/upload -F "file=@data/AT_30_A.gml"
```

---

## 📄 License

MIT License - feel free to use and modify

---

## 🙏 Acknowledgments

- **Three.js** - 3D graphics library
- **Flask** - Python web framework
- **Trimesh** - 3D geometry processing
- **pygltflib** - GLTF/GLB file handling

---

## 📞 Support

For issues or questions:
1. Check **Troubleshooting** section above
2. Review **API Documentation** at http://localhost:5001/api
3. Check server logs for detailed error messages

---

**Built with ❤️ for CityGML visualization**
