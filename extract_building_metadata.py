#!/usr/bin/env python3
"""
Extract building-level attributes from CityGML and enhance existing metadata.
This script reads the CityGML file and extracts:
- bldg:measuredHeight
- bldg:storeysAboveGround
- bldg:storeysBelowGround
- bldg:Building gml:id

It then updates the metadata JSON to include building information and 
maps each surface to its parent building.
"""

import json
import xml.etree.ElementTree as ET
import os

# Paths
GML_FILE = "data/AT_30_A.gml"
METADATA_FILE = "output/citymodel_metadata.json"
OUTPUT_FILE = "output/citymodel_metadata.json"

# Parse the GML file
print("Parsing CityGML file...")
tree = ET.parse(GML_FILE)
root = tree.getroot()

# Namespaces for CityGML 2.0
ns = {
    'core': 'http://www.opengis.net/citygml/2.0',
    'bldg': 'http://www.opengis.net/citygml/building/2.0',
    'gml': 'http://www.opengis.net/gml',
    'gen': 'http://www.opengis.net/citygml/generics/2.0'
}

# Register namespaces for ElementTree
for prefix, uri in ns.items():
    ET.register_namespace(prefix, uri)

# Load existing metadata
print("Loading existing metadata...")
with open(METADATA_FILE, 'r') as f:
    metadata = json.load(f)

# Initialize new structures
buildings_data = {}
surface_to_building_map = {}

# Find all buildings
print("Extracting building attributes...")
buildings = root.findall('.//bldg:Building', namespaces=ns)
print(f"Found {len(buildings)} buildings")

for building in buildings:
    # Get building ID
    building_id = building.get('{http://www.opengis.net/gml}id')
    
    if not building_id:
        continue
    
    # Initialize building data
    building_data = {
        'id': building_id,
        'measuredHeight': None,
        'storeysAboveGround': None,
        'storeysBelowGround': None,
        'surfaces': []
    }
    
    # Extract measured height
    height_elem = building.find('.//bldg:measuredHeight', namespaces=ns)
    if height_elem is not None and height_elem.text:
        try:
            building_data['measuredHeight'] = float(height_elem.text)
        except (ValueError, AttributeError):
            pass
    
    # Extract storeys above ground
    storeys_above = building.find('.//bldg:storeysAboveGround', namespaces=ns)
    if storeys_above is not None and storeys_above.text:
        try:
            building_data['storeysAboveGround'] = int(storeys_above.text)
        except (ValueError, AttributeError):
            pass
    
    # Extract storeys below ground
    storeys_below = building.find('.//bldg:storeysBelowGround', namespaces=ns)
    if storeys_below is not None and storeys_below.text:
        try:
            building_data['storeysBelowGround'] = int(storeys_below.text)
        except (ValueError, AttributeError):
            pass
    
    # Find all surfaces within this building
    surfaces = building.findall('.//*[@{http://www.opengis.net/gml}id]', namespaces=ns)
    for surface in surfaces:
        surface_id = surface.get('{http://www.opengis.net/gml}id')
        if surface_id and surface_id != building_id:
            # Check if this is a surface type (RoofSurface, WallSurface, etc.)
            if any(surf_type in surface.tag for surf_type in ['RoofSurface', 'WallSurface', 'GroundSurface', 'ClosureSurface', 'FloorSurface', 'CeilingSurface']):
                building_data['surfaces'].append(surface_id)
                surface_to_building_map[surface_id] = building_id
    
    buildings_data[building_id] = building_data

print(f"Processed {len(buildings_data)} buildings with attributes")
print(f"Mapped {len(surface_to_building_map)} surfaces to buildings")

# Update metadata structure
print("Updating metadata structure...")

# Create new metadata structure
new_metadata = {
    'offset': metadata.get('offset', {}),
    'total_objects': metadata.get('total_objects', 0),
    'buildings': buildings_data,
    'surfaces': {}
}

# Update existing surface metadata with building references
for obj_id, obj_data in metadata.get('objects', {}).items():
    if obj_data.get('element_type') in ['RoofSurface', 'WallSurface', 'GroundSurface', 'ClosureSurface', 'FloorSurface', 'CeilingSurface']:
        surface_data = {
            'name': obj_data.get('metadata', {}).get('name', obj_id),
            'type': obj_data.get('element_type'),
            'polygonCount': obj_data.get('polygon_count', 0),
            'buildingId': surface_to_building_map.get(obj_id)
        }
        new_metadata['surfaces'][obj_id] = surface_data

print(f"Updated {len(new_metadata['surfaces'])} surface entries")

# Save enhanced metadata
print("Saving enhanced metadata...")
with open(OUTPUT_FILE, 'w') as f:
    json.dump(new_metadata, f, indent=2)

print(f"Enhanced metadata saved to {OUTPUT_FILE}")
print(f"Total buildings: {len(buildings_data)}")
print(f"Total surfaces: {len(new_metadata['surfaces'])}")

# Print a sample
if buildings_data:
    sample_id = list(buildings_data.keys())[0]
    sample = buildings_data[sample_id]
    print(f"\nSample building data for '{sample_id}':")
    print(f"  Height: {sample['measuredHeight']} m")
    print(f"  Storeys Above: {sample['storeysAboveGround']}")
    print(f"  Storeys Below: {sample['storeysBelowGround']}")
    print(f"  Number of surfaces: {len(sample['surfaces'])}")
