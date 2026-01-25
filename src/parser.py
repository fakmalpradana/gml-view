"""
CityGML Parser Module

Extracts geometry data from CityGML files, organizing by gml:id.
"""

from lxml import etree
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CityGMLParser:
    """Parser for CityGML 2.0 files."""
    
    # CityGML 2.0 namespaces
    NAMESPACES = {
        'core': 'http://www.opengis.net/citygml/2.0',
        'gml': 'http://www.opengis.net/gml',
        'bldg': 'http://www.opengis.net/citygml/building/2.0',
        'app': 'http://www.opengis.net/citygml/appearance/2.0',
        'gen': 'http://www.opengis.net/citygml/generics/2.0',
        'xlink': 'http://www.w3.org/1999/xlink'
    }
    
    def __init__(self, file_path: str):
        """Initialize parser with CityGML file path."""
        self.file_path = file_path
        self.tree = None
        self.root = None
        
    def parse(self) -> Dict[str, dict]:
        """
        Parse CityGML file and extract all geometry organized by gml:id.
        
        Returns:
            Dict mapping gml:id to {
                'element_type': str,
                'polygons': [[(x, y, z), ...], ...],
                'metadata': {}
            }
        """
        logger.info(f"Parsing CityGML file: {self.file_path}")
        
        # Parse XML
        self.tree = etree.parse(self.file_path)
        self.root = self.tree.getroot()
        
        # Extract all elements with gml:id
        geometries = {}
        
        # Find all Building elements
        buildings = self.root.xpath('//bldg:Building', namespaces=self.NAMESPACES)
        logger.info(f"Found {len(buildings)} Building elements")
        
        for building in buildings:
            gml_id = building.get('{%s}id' % self.NAMESPACES['gml'])
            if gml_id:
                geo_data = self._extract_geometry(building)
                if geo_data['polygons']:
                    geometries[gml_id] = geo_data
                    logger.debug(f"  Building {gml_id}: {len(geo_data['polygons'])} polygons")
        
        # Find all surface elements (RoofSurface, WallSurface, etc.)
        surface_types = ['RoofSurface', 'WallSurface', 'GroundSurface', 'ClosureSurface']
        for surface_type in surface_types:
            surfaces = self.root.xpath(f'//bldg:{surface_type}', namespaces=self.NAMESPACES)
            logger.info(f"Found {len(surfaces)} {surface_type} elements")
            
            for surface in surfaces:
                gml_id = surface.get('{%s}id' % self.NAMESPACES['gml'])
                if gml_id:
                    geo_data = self._extract_geometry(surface)
                    geo_data['element_type'] = surface_type
                    if geo_data['polygons']:
                        geometries[gml_id] = geo_data
                        logger.debug(f"  {surface_type} {gml_id}: {len(geo_data['polygons'])} polygons")
        
        logger.info(f"Total extracted: {len(geometries)} objects with geometry")
        return geometries
    
    def _extract_geometry(self, element) -> dict:
        """
        Extract geometry from a CityGML element.
        
        Returns:
            {
                'element_type': str,
                'polygons': [[(x, y, z), ...], ...],
                'metadata': {name, description, etc.}
            }
        """
        result = {
            'element_type': element.tag.split('}')[-1],  # Remove namespace
            'polygons': [],
            'metadata': {}
        }
        
        # Extract metadata
        name_elem = element.find('gml:name', namespaces=self.NAMESPACES)
        if name_elem is not None:
            result['metadata']['name'] = name_elem.text
        
        desc_elem = element.find('gml:description', namespaces=self.NAMESPACES)
        if desc_elem is not None:
            result['metadata']['description'] = desc_elem.text
        
        # Extract all polygons
        polygons = element.xpath('.//gml:Polygon', namespaces=self.NAMESPACES)
        
        for polygon in polygons:
            coords = self._extract_polygon_coordinates(polygon)
            if coords:
                result['polygons'].append(coords)
        
        return result
    
    def _extract_polygon_coordinates(self, polygon_element) -> List[Tuple[float, float, float]]:
        """
        Extract coordinates from a gml:Polygon element.
        
        Returns:
            List of (x, y, z) tuples representing polygon vertices.
        """
        coordinates = []
        
        # Find LinearRing (exterior boundary)
        linear_ring = polygon_element.find('.//gml:LinearRing', namespaces=self.NAMESPACES)
        
        if linear_ring is not None:
            # Extract all gml:pos elements
            pos_elements = linear_ring.findall('gml:pos', namespaces=self.NAMESPACES)
            
            for pos in pos_elements:
                if pos.text:
                    # Parse coordinates from text: "x y z"
                    coords = pos.text.strip().split()
                    if len(coords) >= 3:
                        try:
                            x, y, z = float(coords[0]), float(coords[1]), float(coords[2])
                            coordinates.append((x, y, z))
                        except ValueError:
                            logger.warning(f"Invalid coordinates: {pos.text}")
                            continue
            
            # Alternative: posList (space-separated list of coordinates)
            pos_list = linear_ring.find('gml:posList', namespaces=self.NAMESPACES)
            if pos_list is not None and pos_list.text:
                coords = pos_list.text.strip().split()
                # Group by 3 (x, y, z)
                for i in range(0, len(coords), 3):
                    if i + 2 < len(coords):
                        try:
                            x, y, z = float(coords[i]), float(coords[i+1]), float(coords[i+2])
                            coordinates.append((x, y, z))
                        except ValueError:
                            continue
        
        return coordinates
    
    def get_bounds(self) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """
        Get the bounding box from the CityGML envelope.
        
        Returns:
            (min_corner, max_corner) as tuples of (x, y, z)
        """
        envelope = self.root.find('.//gml:Envelope', namespaces=self.NAMESPACES)
        
        if envelope is not None:
            lower = envelope.find('gml:lowerCorner', namespaces=self.NAMESPACES)
            upper = envelope.find('gml:upperCorner', namespaces=self.NAMESPACES)
            
            if lower is not None and upper is not None:
                lower_coords = [float(x) for x in lower.text.strip().split()]
                upper_coords = [float(x) for x in upper.text.strip().split()]
                
                return (tuple(lower_coords), tuple(upper_coords))
        
        return None
