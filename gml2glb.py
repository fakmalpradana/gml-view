#!/usr/bin/env python3
"""
CityGML to GLB/GLTF converter that groups surfaces by Building ID.
Extracts building attributes: storeysAboveGround, storeysBelowGround, measuredHeight, gml:id, description.
"""

import xml.etree.ElementTree as ET
import json
import sys
import struct
from pathlib import Path
from collections import defaultdict

try:
    import numpy as np
except ImportError:
    print("Error: numpy is required. Install with: pip3 install numpy")
    sys.exit(1)

def parse_citygml(gml_file):
    """Parse CityGML and extract buildings with their surfaces grouped by Building ID."""
    tree = ET.parse(gml_file)
    root = tree.getroot()
    
    # Namespaces for CityGML 2.0
    ns = {
        'core': 'http://www.opengis.net/citygml/2.0',
        'bldg': 'http://www.opengis.net/citygml/building/2.0',
        'gml': 'http://www.opengis.net/gml',
        'gen': 'http://www.opengis.net/citygml/generics/2.0'
    }
    
    buildings_data = {}
    
    # Find all buildings
    buildings = root.findall('.//bldg:Building', namespaces=ns)
    print(f"Found {len(buildings)} buildings")
    
    for building in buildings:
        # Get building ID
        building_id = building.get('{http://www.opengis.net/gml}id')
        if not building_id:
            continue
        
        # Initialize or get existing building data
        if building_id not in buildings_data:
            buildings_data[building_id] = {
                'id': building_id,
                'description': None,
                'measuredHeight': None,
                'storeysAboveGround': None,
                'storeysBelowGround': None,
                'surfaces': []
            }
        
        building_info = buildings_data[building_id]
        
        # Update building attributes if found (and not already set)
        desc_elem = building.find('.//gml:description', namespaces=ns)
        if desc_elem is not None and desc_elem.text and not building_info['description']:
            building_info['description'] = desc_elem.text.strip()
        
        height_elem = building.find('.//bldg:measuredHeight', namespaces=ns)
        if height_elem is not None and height_elem.text and not building_info['measuredHeight']:
            try:
                building_info['measuredHeight'] = float(height_elem.text)
            except ValueError:
                pass
        
        storeys_above = building.find('.//bldg:storeysAboveGround', namespaces=ns)
        if storeys_above is not None and storeys_above.text and not building_info['storeysAboveGround']:
            try:
                building_info['storeysAboveGround'] = int(storeys_above.text)
            except ValueError:
                pass
        
        storeys_below = building.find('.//bldg:storeysBelowGround', namespaces=ns)
        if storeys_below is not None and storeys_below.text and not building_info['storeysBelowGround']:
            try:
                building_info['storeysBelowGround'] = int(storeys_below.text)
            except ValueError:
                pass
        
        # Find all semantic surfaces within this building element
        surface_types = [
            ('bldg:RoofSurface', 'RoofSurface'),
            ('bldg:WallSurface', 'WallSurface'),
            ('bldg:GroundSurface', 'GroundSurface'),
            ('bldg:ClosureSurface', 'ClosureSurface'),
            ('bldg:FloorSurface', 'FloorSurface'),
            ('bldg:CeilingSurface', 'CeilingSurface')
        ]
        
        for surface_tag, surface_type in surface_types:
            for surface_elem in building.findall('.//' + surface_tag, namespaces=ns):
                # Find all polygons in this surface
                for polygon in surface_elem.findall('.//gml:Polygon', namespaces=ns):
                    # Get exterior ring
                    exterior = polygon.find('.//gml:exterior', namespaces=ns)
                    if exterior is None:
                        continue
                    
                    # Get LinearRing
                    linear_ring = exterior.find('.//gml:LinearRing', namespaces=ns)
                    if linear_ring is None:
                        continue
                    
                    points = []
                    
                    # Try posList first (batch coordinates)
                    poslist = linear_ring.find('gml:posList', namespaces=ns)
                    if poslist is not None and poslist.text:
                        coords = list(map(float, poslist.text.split()))
                        points = [(coords[i], coords[i+1], coords[i+2]) 
                                 for i in range(0, len(coords), 3)]
                    else:
                        # Try individual pos elements
                        pos_elements = linear_ring.findall('gml:pos', namespaces=ns)
                        for pos in pos_elements:
                            if pos.text:
                                coords = list(map(float, pos.text.split()))
                                if len(coords) >= 3:
                                    points.append((coords[0], coords[1], coords[2]))
                    
                    if len(points) < 3:
                        continue
                    
                    # Append surface to building's surfaces list
                    building_info['surfaces'].append({
                        'type': surface_type,
                        'points': points
                    })
    
    return buildings_data

def calculate_offset(buildings_data):
    """Calculate minimum coordinates for centering."""
    all_points = []
    for building_info in buildings_data.values():
        for surface in building_info['surfaces']:
            all_points.extend(surface['points'])
    
    if not all_points:
        return (0, 0, 0)
    
    min_x = min(p[0] for p in all_points)
    min_y = min(p[1] for p in all_points)
    min_z = min(p[2] for p in all_points)
    
    return (min_x, min_y, min_z)

def triangulate_polygon(points):
    """Simple triangle fan triangulation."""
    if len(points) < 3:
        return []
    
    triangles = []
    for i in range(1, len(points) - 1):
        triangles.append([points[0], points[i], points[i+1]])
    
    return triangles

def create_glb(buildings_data, output_path, offset):
    """Create GLB file with one mesh per building (all surfaces combined)."""
    
    print(f"Creating GLB with {len(buildings_data)} building meshes")
    
    meshes = []
    accessors = []
    buffer_views = []
    buffers_data = []
    
    current_byte_offset = 0
    
    # Create one mesh per building
    for building_id, building_info in buildings_data.items():
        if not building_info['surfaces']:
            continue
        
        # Collect all vertices and indices for this building
        all_vertices = []
        all_indices = []
        vertex_offset = 0
        
        for surface in building_info['surfaces']:
            # Apply offset
            offset_points = [(p[0] - offset[0], p[1] - offset[1], p[2] - offset[2]) 
                            for p in surface['points']]
            
            # Triangulate
            triangles = triangulate_polygon(offset_points)
            
            for tri in triangles:
                for vert in tri:
                    all_vertices.extend(vert)
                
                # Add indices
                for i in range(3):
                    all_indices.append(vertex_offset + i)
                vertex_offset += 3
        
        if not all_vertices:
            continue
        
        # Convert to numpy arrays
        vertices_array = np.array(all_vertices, dtype=np.float32)
        indices_array = np.array(all_indices, dtype=np.uint32)
        
        # Create buffer views and accessors
        # Vertices
        vertex_buffer = vertices_array.tobytes()
        vertex_buffer_view_idx = len(buffer_views)
        buffer_views.append({
            'buffer': 0,
            'byteOffset': current_byte_offset,
            'byteLength': len(vertex_buffer),
            'target': 34962  # ARRAY_BUFFER
        })
        buffers_data.append(vertex_buffer)
        current_byte_offset += len(vertex_buffer)
        
        # Pad to 4-byte boundary
        padding = (4 - (current_byte_offset % 4)) % 4
        if padding:
            buffers_data.append(b'\x00' * padding)
            current_byte_offset += padding
        
        vertex_accessor_idx = len(accessors)
        accessors.append({
            'bufferView': vertex_buffer_view_idx,
            'byteOffset': 0,
            'componentType': 5126,  # FLOAT
            'count': len(all_vertices) // 3,
            'type': 'VEC3',
            'min': [float(min(all_vertices[i::3])) for i in range(3)],
            'max': [float(max(all_vertices[i::3])) for i in range(3)]
        })
        
        # Indices
        index_buffer = indices_array.tobytes()
        index_buffer_view_idx = len(buffer_views)
        buffer_views.append({
            'buffer': 0,
            'byteOffset': current_byte_offset,
            'byteLength': len(index_buffer),
            'target': 34963  # ELEMENT_ARRAY_BUFFER
        })
        buffers_data.append(index_buffer)
        current_byte_offset += len(index_buffer)
        
        # Pad to 4-byte boundary
        padding = (4 - (current_byte_offset % 4)) % 4
        if padding:
            buffers_data.append(b'\x00' * padding)
            current_byte_offset += padding
        
        index_accessor_idx = len(accessors)
        accessors.append({
            'bufferView': index_buffer_view_idx,
            'byteOffset': 0,
            'componentType': 5125,  # UNSIGNED_INT
            'count': len(all_indices),
            'type': 'SCALAR'
        })
        
        # Create mesh with building ID as name
        meshes.append({
            'name': building_id,  # CRITICAL: Building ID as mesh name
            'primitives': [{
                'attributes': {
                    'POSITION': vertex_accessor_idx
                },
                'indices': index_accessor_idx,
                'mode': 4  # TRIANGLES
            }]
        })
    
    # Combine all buffer data
    combined_buffer = b''.join(buffers_data)
    
    # Create JSON structure
    gltf_json = {
        'asset': {
            'version': '2.0',
            'generator': 'CityGML2GLB Converter v2'
        },
        'scene': 0,
        'scenes': [{
            'nodes': list(range(len(meshes)))
        }],
        'nodes': [{'mesh': i, 'name': meshes[i]['name']} for i in range(len(meshes))],
        'meshes': meshes,
        'accessors': accessors,
        'bufferViews': buffer_views,
        'buffers': [{
            'byteLength': len(combined_buffer)
        }]
    }
    
    # Write GLB file
    write_glb(output_path, gltf_json, combined_buffer)
    print(f"Wrote GLB to {output_path}")

def write_glb(output_path, gltf_json, binary_buffer):
    """Write GLB file (binary GLTF)."""
    # Convert JSON to bytes
    json_bytes = json.dumps(gltf_json, separators=(',', ':')).encode('utf-8')
    
    # Pad JSON to 4-byte boundary
    json_padding = (4 - (len(json_bytes) % 4)) % 4
    json_bytes += b' ' * json_padding
    
    # Pad binary to 4-byte boundary
    bin_padding = (4 - (len(binary_buffer) % 4)) % 4
    binary_buffer += b'\x00' * bin_padding
    
    # GLB header
    magic = 0x46546C67  # 'glTF'
    version = 2
    total_length = 12 + 8 + len(json_bytes) + 8 + len(binary_buffer)
    
    with open(output_path, 'wb') as f:
        # Header
        f.write(struct.pack('<III', magic, version, total_length))
        
        # JSON chunk
        f.write(struct.pack('<I', len(json_bytes)))
        f.write(struct.pack('<I', 0x4E4F534A))  # 'JSON'
        f.write(json_bytes)
        
        # Binary chunk
        f.write(struct.pack('<I', len(binary_buffer)))
        f.write(struct.pack('<I', 0x004E4942))  # 'BIN\0'
        f.write(binary_buffer)

def write_metadata(buildings_data, metadata_file, offset):
    """Write metadata JSON compatible with viewer."""
    metadata = {
        'offset': {
            'x': offset[0],
            'y': offset[1],
            'z': offset[2]
        },
        'total_objects': len(buildings_data),
        'objects': {}
    }
    
    # Create metadata for each building
    for building_id, building_info in buildings_data.items():
        # Count surfaces by type
        surface_types = defaultdict(int)
        for surface in building_info['surfaces']:
            surface_types[surface['type']] += 1
        
        metadata['objects'][building_id] = {
            'element_type': 'Building',
            'polygon_count': len(building_info['surfaces']),
            'metadata': {
                'name': building_id,
                'description': building_info.get('description', f"{building_id}, created from CityGML"),
                'measuredHeight': building_info.get('measuredHeight'),
                'storeysAboveGround': building_info.get('storeysAboveGround'),
                'storeysBelowGround': building_info.get('storeysBelowGround'),
                'surfaceTypes': dict(surface_types)
            }
        }
    
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Wrote metadata to {metadata_file}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python gml2glb.py <input.gml> [output.glb]")
        sys.exit(1)
    
    gml_file = sys.argv[1]
    
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        base_name = Path(gml_file).stem
        output_file = f"{base_name}.glb"
    
    metadata_file = output_file.replace('.glb', '_metadata.json')
    
    print(f"Converting {gml_file} to GLB...")
    buildings_data = parse_citygml(gml_file)
    
    if not buildings_data:
        print("No buildings found!")
        sys.exit(1)
    
    print(f"Parsed {len(buildings_data)} buildings")
    
    # Check total surfaces
    total_surfaces = sum(len(b['surfaces']) for b in buildings_data.values())
    print(f"Total surfaces: {total_surfaces}")
    
    if total_surfaces == 0:
        print("No surfaces found in buildings!")
        sys.exit(1)
    
    offset = calculate_offset(buildings_data)
    print(f"Offset: {offset}")
    
    create_glb(buildings_data, output_file, offset)
    write_metadata(buildings_data, metadata_file, offset)
    
    print(f"✅ Done! Created {output_file} and {metadata_file}")

if __name__ == "__main__":
    main()
