# CityGML Conversion API Documentation

## 🚀 Quick Start

### Access API Documentation
- **OpenAPI Spec**: http://localhost:5001/api-docs
- **Interactive Docs**: Paste the spec into [Swagger Editor](https://editor.swagger.io/)

### Health Check
```bash
curl http://localhost:5001/health
```

## 📡 API Endpoints

### 1. Upload & Convert CityGML

**Endpoint**: `POST /upload`

**Request**:
```bash
curl -X POST http://localhost:5001/upload \
  -F "file=@data/AT_30_A.gml"
```

**Response**:
```json
{
  "session_id": "14a566b6-b39f-46e5-9e4a-c10c043b6004",
  "filename": "AT_30_A.gml",
  "message": "Conversion successful",
  "files": {
    "glb": "/models/14a566b6-b39f-46e5-9e4a-c10c043b6004/model.glb",
    "metadata": "/models/14a566b6-b39f-46e5-9e4a-c10c043b6004/model_metadata.json"
  }
}
```

### 2. Download GLB Model

**Endpoint**: `GET /models/{session_id}/model.glb`

```bash
curl -O http://localhost:5001/models/{session_id}/model.glb
```

### 3. Download Metadata

**Endpoint**: `GET /models/{session_id}/model_metadata.json`

```bash
curl http://localhost:5001/models/{session_id}/model_metadata.json
```

### 4. Cleanup Session

**Endpoint**: `DELETE /cleanup/{session_id}`

```bash
curl -X DELETE http://localhost:5001/cleanup/{session_id}
```

### 5. List Active Sessions

**Endpoint**: `GET /sessions`

```bash
curl http://localhost:5001/sessions
```

### 6. Cleanup All Sessions

**Endpoint**: `DELETE /cleanup-all`

```bash
curl -X DELETE http://localhost:5001/cleanup-all
```

## 📊 Metadata Format

The metadata JSON contains building information:

```json
{
  "offset": {
    "x": 713367.02599,
    "y": 9313574.202901,
    "z": 3.613178
  },
  "total_objects": 460,
  "objects": {
    "AT_30_A_713388_9313715": {
      "element_type": "Building",
      "polygon_count": 35,
      "metadata": {
        "name": "AT_30_A_713388_9313715",
        "description": "Building description",
        "measuredHeight": 12.5,
        "storeysAboveGround": 3,
        "storeysBelowGround": 0,
        "surfaceTypes": {
          "RoofSurface": 2,
          "WallSurface": 8,
          "GroundSurface": 1
        }
      }
    }
  }
}
```

## 🔧 Python Client Example

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
glb_response = requests.get(glb_url)
with open('model.glb', 'wb') as f:
    f.write(glb_response.content)

# Download metadata
metadata_url = f"http://localhost:5001{result['files']['metadata']}"
metadata = requests.get(metadata_url).json()
print(f"Buildings: {metadata['total_objects']}")

# Cleanup
requests.delete(f'http://localhost:5001/cleanup/{session_id}')
```

## 🌐 JavaScript Client Example

```javascript
// Upload CityGML
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:5001/upload', {
    method: 'POST',
    body: formData
});

const result = await response.json();

// Load GLB with Three.js
const gltfLoader = new GLTFLoader();
gltfLoader.load(
    `http://localhost:5001${result.files.glb}`,
    (gltf) => {
        scene.add(gltf.scene);
    }
);

// Load metadata
const metadata = await fetch(
    `http://localhost:5001${result.files.metadata}`
).then(r => r.json());

// Cleanup when done
await fetch(`http://localhost:5001/cleanup/${result.session_id}`, {
    method: 'DELETE'
});
```

## ⚙️ Error Handling

### Common Errors

**400 Bad Request**:
```json
{
  "error": "Invalid file type. Only .gml and .xml files are allowed"
}
```

**404 Not Found**:
```json
{
  "error": "Session not found"
}
```

**500 Internal Server Error**:
```json
{
  "error": "Conversion failed: <reason>"
}
```

## 📝 Notes

- Maximum conversion timeout: 5 minutes
- Session files auto-cleanup on DELETE
- GLB files are optimized for web (70-80% smaller than OBJ)
- All responses use JSON format
- CORS enabled for local development

## 🔗 Resources

- **OpenAPI Editor**: https://editor.swagger.io/
- **Swagger Inspector**: https://inspector.swagger.io/
- **Postman**: Import OpenAPI spec for testing
