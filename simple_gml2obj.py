#!/usr/bin/env python3
"""
Simple CityGML to OBJ converter that preserves individual surface GML IDs.
Each surface gets its own group in the OBJ file.
"""

import xml.etree.ElementTree as ET
import json
import sys

def parse_citygml(gml_file):
    """Parse CityGML and extract all surfaces with their IDs."""
    tree = ET.parse(gml_file)
    root = tree.getroot()
    
    # Register namespaces
    ET.register_namespace('', 'http://www.opengis.net/citygml/2.0')
    ET.register_namespace('gml', 'http://www.opengis.net/gml')
    ET.register_namespace('bldg', 'http://www.opengis.net/citygml/building/2.0')
    
    surfaces = []
    vertex_index = 1
    
    # Find all semantic surfaces (RoofSurface, WallSurface, GroundSurface, etc.)
    surface_types = [
        '{http://www.opengis.net/citygml/building/2.0}RoofSurface',
        '{http://www.opengis.net/citygml/building/2.0}WallSurface',
        '{http://www.opengis.net/citygml/building/2.0}GroundSurface',
        '{http://www.opengis.net/citygml/building/2.0}ClosureSurface',
    ]
    
    for surface_type in surface_types:
        for surface_elem in root.findall('.//' + surface_type):
            gml_id = surface_elem.get('{http://www.opengis.net/gml}id')
            if not gml_id:
                continue
            
            # Find all polygons in this surface
            for polygon in surface_elem.findall('.//{http://www.opengis.net/gml}Polygon'):
                # Get exterior ring
                exterior = polygon.find('.//{http://www.opengis.net/gml}exterior')
                if exterior is None:
                    continue
                
                # Get pos list
                poslist = exterior.find('.//{http://www.opengis.net/gml}posList')
                if poslist is None or not poslist.text:
                    continue
                
                # Parse coordinates
                coords = list(map(float, poslist.text.split()))
                points = [(coords[i], coords[i+1], coords[i+2]) 
                         for i in range(0, len(coords), 3)]
                
                if len(points) < 3:
                    continue
                
                # Store surface info
                surfaces.append({
                    'id': gml_id,
                    'type': surface_type.split('}')[1],  # Extract type name
                    'points': points,
                    'start_vertex': vertex_index
                })
                
                vertex_index += len(points)
    
    return surfaces

def calculate_offset(surfaces):
    """Calculate the minimum coordinates for offset."""
    if not surfaces:
        return (0, 0, 0)
    
    all_points = []
    for surface in surfaces:
        all_points.extend(surface['points'])
    
    min_x = min(p[0] for p in all_points)
    min_y = min(p[1] for p in all_points)
    min_z = min(p[2] for p in all_points)
    
    return (min_x, min_y, min_z)

def write_obj(surfaces, obj_file, mtl_file, offset):
    """Write OBJ file with individual groups for each surface."""
    
    with open(obj_file, 'w') as f:
        # Header
        f.write("# CityGML to OBJ Conversion\\n")
        f.write(f"# Total objects: {len(surfaces)}\\n")
        f.write(f"# Center offset: {offset}\\n")
        f.write(f"mtllib {mtl_file}\\n\\n")
        
        vertex_count = 1
        
        for surface in surfaces:
            # Write group name (GML ID)
            f.write(f"\\ng {surface['id']}\\n")
            f.write("usemtl building\\n\\n")
            
            # Write vertices
            for point in surface['points']:
                x, y, z = point
                x -= offset[0]
                y -= offset[1]
                z -= offset[2]
                f.write(f"v {x} {y} {z}\\n")
            
            # Write faces (triangulation for polygons > 3 vertices)
            num_verts = len(surface['points'])
            if num_verts == 3:
                # Triangle
                f.write(f"f {vertex_count} {vertex_count+1} {vertex_count+2}\\n")
            elif num_verts == 4:
                # Quad -> 2 triangles
                f.write(f"f {vertex_count} {vertex_count+1} {vertex_count+2}\\n")
                f.write(f"f {vertex_count} {vertex_count+2} {vertex_count+3}\\n")
            else:
                # Triangle fan for n-gons
                for i in range(1, num_verts - 1):
                    f.write(f"f {vertex_count} {vertex_count+i} {vertex_count+i+1}\\n")
            
            f.write("\\n")
            vertex_count += num_verts
    
    print(f"Wrote {len(surfaces)} surfaces to {obj_file}")

def write_mtl(mtl_file):
    """Write simple MTL file."""
    with open(mtl_file, 'w') as f:
        f.write("# Material file\\n\\n")
        f.write("newmtl building\\n")
        f.write("Ka 0.5 0.5 0.5\\n")
        f.write("Kd 0.7 0.7 0.7\\n")
        f.write("Ks 0.1 0.1 0.1\\n")
        f.write("Ns 10.0\\n")
        f.write("illum 2\\n")

def write_metadata(surfaces, metadata_file, offset):
    """Write metadata JSON."""
    metadata = {
        'offset': {
            'x': offset[0],
            'y': offset[1],
            'z': offset[2]
        },
        'total_objects': len(surfaces),
        'objects': {}
    }
    
    for surface in surfaces:
        metadata['objects'][surface['id']] = {
            'element_type': 'Surface',
            'polygon_count': 1,
            'metadata': {
                'name': surface['id']
            }
        }
    
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Wrote metadata to {metadata_file}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python simple_gml2obj.py <input.gml>")
        sys.exit(1)
    
    gml_file = sys.argv[1]
    base_name = gml_file.rsplit('.', 1)[0]
    obj_file = f"{base_name}_simple.obj"
    mtl_file = f"{base_name}_simple.mtl"
    metadata_file = f"{base_name}_simple _metadata.json"
    
    print(f"Converting {gml_file}...")
    surfaces = parse_citygml(gml_file)
    print(f"Found {len(surfaces)} surfaces")
    
    if not surfaces:
        print("No surfaces found!")
        sys.exit(1)
    
    offset = calculate_offset(surfaces)
    print(f"Offset: {offset}")
    
    write_obj(surfaces, obj_file, mtl_file, offset)
    write_mtl(mtl_file)
    write_metadata(surfaces, metadata_file, offset)
    
    print("Done!")

if __name__ == "__main__":
    main()
