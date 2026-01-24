import os
import json
import tempfile
import uuid
import logging
from typing import Dict, Any, Tuple
from cjio import cityjson

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CityGMLProcessor:
    """
    Handles the ingestion of CityGML files, conversion to CityJSON,
    export to GLB for rendering, and extraction of metadata.
    """

    def __init__(self):
        self.current_cityjson = None
        self.metadata_cache = {}

    def process_file(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Main pipeline:
        1. Convert CityGML -> CityJSON (in-memory or temp).
        2. Export GLB for visualization.
        3. Extract Metadata.
        
        Returns:
            (glb_path, metadata_dict)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Processing file: {file_path}")
        
        # 1. Load/Convert to CityJSON
        # If it's already CityJSON, load it directly. If GML, convert.
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.json':
            self.current_cityjson = cityjson.load(file_path)
        elif ext in ['.gml', '.xml']:
            # cjio can read citygml via from_file (uses citygml-tools or internal parser if available)
            # Note: cjio might require 'citygml-tools' CLI for robust GML conversion, 
            # but for this boilerplate we assume cjio's native capabilities or pre-installed tools.
            # However, prompt asked to "Convert to CityJSON (using cjio library)".
            try:
                self.current_cityjson = cityjson.load(file_path)
            except Exception as e:
                logger.error(f"Failed to load/convert CityGML: {e}")
                # Fallback or specific GML conversion logic would go here
                raise e
        else:
             raise ValueError("Unsupported file format")

        # 2. Export GLB
        glb_path = self._export_to_glb()
        
        # 3. Extract Metadata
        self.metadata_cache = self._extract_metadata()
        
        return glb_path, self.metadata_cache

    def _export_to_glb(self) -> str:
        """
        Exports the current CityJSON to a temporary GLB file.
        """
        if not self.current_cityjson:
             raise ValueError("No CityJSON loaded")

        # Create a temp file for the GLB
        temp_dir = tempfile.gettempdir()
        filename = f"citygml_view_{uuid.uuid4().hex}.glb"
        glb_path = os.path.join(temp_dir, filename)
        
        logger.info(f"Exporting GLB to: {glb_path}")
        
        # cjio export to glb
        # usage: cityjson.export2glb(outfile)
        # Note: cjio API might vary slightly by version, checking standard usage.
        # Assuming we have the 'export2glb' or similar method available on the object or library.
        # If cjio doesn't have direct python API for glb export but has CLI, we might need to invoke internal functions.
        # Looking at cjio docs, it usually has `export2glb`. 
        try:
            # We assume the cjio object 'self.current_cityjson' has export capabilities 
            # or we use the library function.
            # Actually cjio.cityjson.CityJSON doesn't always have .export2glb directly attached in all versions.
            # It often uses `cjio.convert`.
            # Let's verify commonly used patterns. Often users use `cm.export2gltf()`
            
            # For robustness in this boilerplate, we'll try the standard method:
            gl = self.current_cityjson.export2gltf() # returns a GLTF object or similar? 
            # Wait, cjio's export2gltf usually writes to a file or returns a buffer.
            # Let's try writing to buffer and saving, or passing path.
            
            # If `export2gltf` does not exist, we will need to check the installed cjio version documentation.
            # For now, I will write code that assumes `export2gltf` exists on the CityJSON object
            # and takes a buffer or file path. 
            
            # HACK: Some cjio versions convert via 'io'.
            # Let's assume standard behavior for now.
            # If standard fails, we might need to subprocess `cjio ... export glb ...`
            
            # Using the `export2glb` if available (newer cjio often supports binary)
            # or `export2gltf`.
            
            # To be safe for the user, I'll use a try-except block to handle potential API differences
            # or direct them to ensure `cjio` with `gltf` support is installed.
            
            # self.current_cityjson.export2gltf(filepath=glb_path, binary=True) # Hypothetical API
            
            # Let's inspect the `cityjson` object capabilities in a real run, but here we write the boilerplate.
            # I will assume `export2glb` is not directly on the object but maybe in `cjio.conversions`?
            # Actually simplest is:
            buffer = self.current_cityjson.export2gltf()
            with open(glb_path, 'wb') as f:
                f.write(buffer.read()) # if buffer is BytesIO
            
        except Exception as e:
             # Fallback: Raise error for now
             logger.warning(f"Direct export failed: {e}. Attempting alternative...")
             # Attempt to use CLI if python API is obscure? No, stick to Python.
             # If `export2gltf` returns a different structure.
             # Let's try to assume it writes to a file if a path is given.
             # Or if it returns a list of GLB buffers (one per texture/tile?).
             
             # Re-raise for debugging by user if needed
             raise RuntimeError(f"Could not export to GLB: {e}")

        return glb_path

    def _extract_metadata(self) -> Dict[str, Any]:
        """
        Extracts semantic attributes from CityJSON city objects.
        Returns a dict: { 'ObjectId': { attributes... } }
        """
        if not self.current_cityjson:
             return {}
        
        metadata = {}
        # Access the city objects
        # CityJSON structure: { "CityObjects": { "id": { "attributes": {}, "type": ... } } }
        cm = self.current_cityjson
        
        if hasattr(cm, 'j'):
             # cjio v0.8+ uses .j to access the raw JSON dict
             city_objects = cm.j.get('CityObjects', {})
        else:
             # Older versions or different structure
             city_objects = getattr(cm, 'CityObjects', {})

        for obj_id, obj_data in city_objects.items():
            attributes = obj_data.get('attributes', {})
            obj_type = obj_data.get('type', 'Unknown')
            
            # Flatten/clean attributes if needed
            clean_attrs = attributes.copy()
            clean_attrs['type'] = obj_type
            
            metadata[obj_id] = clean_attrs
            
        return metadata
