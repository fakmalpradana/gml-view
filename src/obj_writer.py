"""
OBJ File Writer Module

Exports geometry to Wavefront OBJ format with materials.
"""

import os
import logging
from typing import Dict
from geometry import GeometryProcessor

logger = logging.getLogger(__name__)


class OBJWriter:
    """Write geometry to OBJ format."""
    
    def __init__(self, geometry_processor: GeometryProcessor):
        self.processor = geometry_processor
        self.vertex_count = 0
        self.normal_count = 0
        
    def write_single_obj(self, geometries: dict, output_path: str, offset: tuple):
        """
        Write all geometries to a single OBJ file with groups.
        
        Args:
            geometries: Dict of {gml_id: {polygons, element_type, metadata}}
            output_path: Output OBJ file path
            offset: Original center offset for metadata
        """
        logger.info(f"Writing OBJ file: {output_path}")
        
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Create MTL file
        mtl_filename = os.path.splitext(os.path.basename(output_path))[0] + '.mtl'
        mtl_path = os.path.join(output_dir, mtl_filename)
        self._write_mtl_file(mtl_path)
        
        with open(output_path, 'w') as f:
            # Header
            f.write("# CityGML to OBJ Conversion\n")
            f.write(f"# Total objects: {len(geometries)}\n")
            f.write(f"# Center offset: {offset}\n")
            f.write(f"mtllib {mtl_filename}\n\n")
            
            self.vertex_count = 1  # OBJ uses 1-based indexing
            self.normal_count = 1
            
            # Write each geometry as a group
            for gml_id, geo_data in geometries.items():
                self._write_group(f, gml_id, geo_data)
        
        logger.info(f"Successfully wrote {len(geometries)} objects to {output_path}")
        
        # Write metadata
        metadata_path = output_path.replace('.obj', '_metadata.json')
        self._write_metadata(metadata_path, geometries, offset)
    
    def _write_group(self, f, gml_id: str, geo_data: dict):
        """Write a single group to the OBJ file."""
        element_type = geo_data['element_type']
        polygons = geo_data['polygons']
        
        # Group header
        f.write(f"\n# {gml_id} ({element_type})\n")
        f.write(f"g {gml_id}\n")
        
        # Set material
        material = self.processor.get_material_for_type(element_type)
        f.write(f"usemtl {material}\n\n")
        
        # Collect all vertices and faces for this group
        group_vertices = []
        group_normals = []
        group_faces = []
        
        vertex_offset = 0
        
        for polygon in polygons:
            if len(polygon) < 3:
                continue
            
            # Add vertices
            for vertex in polygon:
                group_vertices.append(vertex)
                f.write(f"v {vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f}\n")
            
            # Triangulate polygon
            triangles = self.processor.triangulate_polygon(polygon)
            
            for tri_indices in triangles:
                # Calculate normal for this triangle
                v0 = polygon[tri_indices[0]]
                v1 = polygon[tri_indices[1]]
                v2 = polygon[tri_indices[2]]
                
                normal = self.processor.calculate_normal(v0, v1, v2)
                group_normals.append(normal)
                
                # Write normal
                f.write(f"vn {normal[0]:.6f} {normal[1]:.6f} {normal[2]:.6f}\n")
                
                # Adjust indices to global vertex count
                face_indices = [
                    self.vertex_count + vertex_offset + tri_indices[0],
                    self.vertex_count + vertex_offset + tri_indices[1],
                    self.vertex_count + vertex_offset + tri_indices[2]
                ]
                
                group_faces.append(face_indices)
            
            vertex_offset += len(polygon)
        
        # Write faces
        f.write("\n")
        for i, face in enumerate(group_faces):
            normal_idx = self.normal_count + i
            # OBJ format: f v1//n1 v2//n2 v3//n3 (vertex//normal)
            f.write(f"f {face[0]}//{normal_idx} {face[1]}//{normal_idx} {face[2]}//{normal_idx}\n")
        
        # Update counters
        self.vertex_count += len(group_vertices)
        self.normal_count += len(group_faces)
    
    def _write_mtl_file(self, mtl_path: str):
        """Write material library file."""
        logger.info(f"Writing MTL file: {mtl_path}")
        
        with open(mtl_path, 'w') as f:
            f.write("# CityGML Materials\n\n")
            
            # Roof material (red/terracotta)
            f.write("newmtl roof\n")
            f.write("Ka 0.8 0.3 0.2\n")  # Ambient
            f.write("Kd 0.8 0.3 0.2\n")  # Diffuse
            f.write("Ks 0.2 0.2 0.2\n")  # Specular
            f.write("Ns 50.0\n\n")        # Shininess
            
            # Wall material (light gray)
            f.write("newmtl wall\n")
            f.write("Ka 0.7 0.7 0.7\n")
            f.write("Kd 0.7 0.7 0.7\n")
            f.write("Ks 0.3 0.3 0.3\n")
            f.write("Ns 30.0\n\n")
            
            # Ground material (brown)
            f.write("newmtl ground\n")
            f.write("Ka 0.5 0.4 0.3\n")
            f.write("Kd 0.5 0.4 0.3\n")
            f.write("Ks 0.1 0.1 0.1\n")
            f.write("Ns 20.0\n\n")
            
            # Closure material (blue)
            f.write("newmtl closure\n")
            f.write("Ka 0.3 0.4 0.7\n")
            f.write("Kd 0.3 0.4 0.7\n")
            f.write("Ks 0.2 0.2 0.2\n")
            f.write("Ns 40.0\n\n")
            
            # Building material (neutral)
            f.write("newmtl building\n")
            f.write("Ka 0.6 0.6 0.6\n")
            f.write("Kd 0.6 0.6 0.6\n")
            f.write("Ks 0.2 0.2 0.2\n")
            f.write("Ns 30.0\n\n")
            
            # Default material
            f.write("newmtl default\n")
            f.write("Ka 0.5 0.5 0.5\n")
            f.write("Kd 0.5 0.5 0.5\n")
            f.write("Ks 0.2 0.2 0.2\n")
            f.write("Ns 25.0\n")
    
    def _write_metadata(self, metadata_path: str, geometries: dict, offset: tuple):
        """Write metadata JSON file."""
        import json
        
        metadata = {
            'offset': {
                'x': offset[0],
                'y': offset[1],
                'z': offset[2]
            },
            'total_objects': len(geometries),
            'objects': {}
        }
        
        for gml_id, geo_data in geometries.items():
            metadata['objects'][gml_id] = {
                'element_type': geo_data['element_type'],
                'polygon_count': len(geo_data['polygons']),
                'metadata': geo_data.get('metadata', {})
            }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Metadata written to {metadata_path}")
