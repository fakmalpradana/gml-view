#!/usr/bin/env python3
"""
CityGML Conversion Server
Handles file uploads, automatic conversion to GLB, and temporary file management
"""

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import os
import sys
import json
import tempfile
import shutil
import subprocess
import uuid
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for local development

# Configuration
TEMP_DIR = Path("temp_models")
UPLOAD_DIR = Path("uploads")
TEMP_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)

# Store active conversions
active_models = {}

@app.route('/api', methods=['GET'])
def swagger_ui():
    """Serve Swagger UI page"""
    try:
        ui_path = Path(__file__).parent / 'docs' / 'swagger_ui.html'
        return send_file(ui_path, mimetype='text/html')
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route('/api-docs', methods=['GET'])
def api_docs():
    """Serve OpenAPI documentation"""
    try:
        docs_path = Path(__file__).parent / 'docs' / 'openapi.yaml'
        return send_file(docs_path, mimetype='text/yaml')
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "Conversion server is running"})

@app.route('/upload', methods=['POST'])
def upload_gml():
    """
    Upload and convert a CityGML file.
    Returns a session ID for accessing the converted files.
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Empty filename"}), 400
        
        # Validate file extension
        if not file.filename.lower().endswith(('.gml', '.xml')):
            return jsonify({"error": "Invalid file type. Only .gml and .xml files are allowed"}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create session directory
        session_dir = TEMP_DIR / session_id
        session_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        gml_path = UPLOAD_DIR / f"{session_id}_{file.filename}"
        file.save(gml_path)
        
        print(f"[{timestamp}] Uploaded: {file.filename} (Session: {session_id})")
        
        # Run conversion
        print(f"[{timestamp}] Starting conversion...")
        success, message = run_conversion(gml_path, session_dir, session_id)
        
        if not success:
            # Cleanup on failure
            shutil.rmtree(session_dir, ignore_errors=True)
            gml_path.unlink(missing_ok=True)
            return jsonify({"error": message}), 500
        
        # Store session info
        active_models[session_id] = {
            "filename": file.filename,
            "created": timestamp,
            "gml_path": str(gml_path),
            "session_dir": str(session_dir)
        }
        
        print(f"[{timestamp}] Conversion successful!")
        return jsonify({
            "session_id": session_id,
            "filename": file.filename,
            "message": "Conversion successful",
            "files": {
                "glb": f"/models/{session_id}/model.glb",
                "metadata": f"/models/{session_id}/model_metadata.json"
            }
        }), 200
        
    except Exception as e:
        print(f"Error during upload: {str(e)}")
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

def run_conversion(gml_path, output_dir, session_id):
    """
    Run the CityGML to GLB conversion script.
    Returns (success: bool, message: str)
    """
    try:
        # Check if conversion script exists
        convert_script = Path("gml2glb.py")
        if not convert_script.exists():
            return False, "Conversion script (gml2glb.py) not found"
        
        # Output file path
        glb_output = output_dir / "model.glb"
        
        # Run conversion
        cmd = [
            sys.executable,
            str(convert_script),
            str(gml_path),
            str(glb_output)
        ]
        
        print(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown error"
            print(f"Conversion failed: {error_msg}")
            return False, f"Conversion failed: {error_msg}"
        
        # Print conversion output
        if result.stdout:
            print(f"Conversion output:\\n{result.stdout}")
        
        # Verify output files exist
        glb_file = output_dir / "model.glb"
        metadata_file = output_dir / "model_metadata.json"
        
        if not glb_file.exists():
            return False, "GLB file was not generated"
        
        if not metadata_file.exists():
            return False, "Metadata file was not generated"
        
        print(f"✅ GLB conversion successful: {glb_file.stat().st_size} bytes")
        print(f"✅ Metadata generated: {metadata_file.stat().st_size} bytes")
        
        return True, "Success"
        
    except subprocess.TimeoutExpired:
        return False, "Conversion timeout (exceeded 5 minutes)"
    except Exception as e:
        return False, f"Conversion error: {str(e)}"

@app.route('/models/<session_id>/<filename>', methods=['GET'])
def serve_model(session_id, filename):
    """Serve converted model files"""
    try:
        session_dir = TEMP_DIR / session_id
        if not session_dir.exists():
            return jsonify({"error": "Session not found"}), 404
        
        return send_from_directory(session_dir, filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/static/<path:filename>', methods=['GET'])
def serve_static(filename):
    """Serve static CSS/JS files"""
    try:
        static_dir = Path(__file__).parent / 'static'
        return send_from_directory(static_dir, filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route('/cleanup/<session_id>', methods=['DELETE'])
def cleanup_session(session_id):
    """Delete temporary files for a session"""
    try:
        if session_id not in active_models:
            return jsonify({"error": "Session not found"}), 404
        
        # Get session info
        session_info = active_models[session_id]
        
        # Delete session directory
        session_dir = Path(session_info["session_dir"])
        if session_dir.exists():
            shutil.rmtree(session_dir)
        
        # Delete uploaded GML file
        gml_path = Path(session_info["gml_path"])
        if gml_path.exists():
            gml_path.unlink()
        
        # Remove from active sessions
        del active_models[session_id]
        
        print(f"Cleaned up session: {session_id}")
        return jsonify({"message": "Session cleaned up successfully"}), 200
        
    except Exception as e:
        print(f"Cleanup error: {str(e)}")
        return jsonify({"error": f"Cleanup failed: {str(e)}"}), 500

@app.route('/sessions', methods=['GET'])
def list_sessions():
    """List all active sessions"""
    return jsonify({
        "sessions": active_models,
        "count": len(active_models)
    })

@app.route('/cleanup-all', methods=['DELETE'])
def cleanup_all():
    """Cleanup all temporary files"""
    try:
        count = 0
        for session_id in list(active_models.keys()):
            try:
                session_info = active_models[session_id]
                
                # Delete directories
                session_dir = Path(session_info["session_dir"])
                if session_dir.exists():
                    shutil.rmtree(session_dir)
                
                gml_path = Path(session_info["gml_path"])
                if gml_path.exists():
                    gml_path.unlink()
                
                del active_models[session_id]
                count += 1
            except Exception as e:
                print(f"Error cleaning session {session_id}: {e}")
        
        return jsonify({
            "message": f"Cleaned up {count} sessions",
            "count": count
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("CityGML Conversion Server")
    print("=" * 60)
    print(f"Temporary files: {TEMP_DIR.absolute()}")
    print(f"Upload directory: {UPLOAD_DIR.absolute()}")
    print("\nEndpoints:")
    print("  GET  /api            - 📖 Swagger UI (Interactive API docs)")
    print("  GET  /api-docs       - OpenAPI specification (YAML)")
    print("  GET  /health         - Health check")
    print("  POST /upload         - Upload and convert GML file")
    print("  GET  /models/<id>/<file> - Serve converted files")
    print("  DELETE /cleanup/<id> - Delete session files")
    print("  GET  /sessions       - List active sessions")
    print("  DELETE /cleanup-all  - Delete all temporary files")
    print("\n🚀 Interactive API Documentation: http://localhost:5001/api")
    print("Starting server on http://localhost:5001")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5001, debug=True)
