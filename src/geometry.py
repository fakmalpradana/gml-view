"""
Geometry Processing Module

Handles coordinate transformations, triangulation, and normal calculations.
"""

import numpy as np
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class GeometryProcessor:
    """Process geometry for 3D export."""
    
    def __init__(self):
        self.offset = (0, 0, 0)
        
    def center_coordinates(self, all_geometries: dict) -> Tuple[dict, Tuple[float, float, float]]:
        """
        Center all coordinates around the origin and transform to Y-forward, Z-up system.
        
        CityGML uses: X=east, Y=north, Z=elevation
        Output uses: X=east, Y=forward(north), Z=up(elevation)
        
        Args:
            all_geometries: Dict of {gml_id: {polygons: [...]}}
            
        Returns:
            (centered_geometries, offset)
        """
        # Collect all vertices
        all_vertices = []
        
        for geo_data in all_geometries.values():
            for polygon in geo_data['polygons']:
                all_vertices.extend(polygon)
        
        if not all_vertices:
            logger.warning("No vertices found")
            return all_geometries, (0, 0, 0)
        
        # Calculate bounding box
        vertices_array = np.array(all_vertices)
        min_corner = vertices_array.min(axis=0)
        max_corner = vertices_array.max(axis=0)
        
        # Calculate center
        center = (min_corner + max_corner) / 2.0
        self.offset = tuple(center)
        
        logger.info(f"Bounding box: min={min_corner}, max={max_corner}")
        logger.info(f"Center offset: {self.offset}")
        logger.info(f"Coordinate system: X=east, Y=forward(north), Z=up(elevation)")
        
        # Apply offset and transform coordinates
        # CityGML: (X, Y, Z) = (east, north, elevation)
        # Output: (X, Y, Z) = (east, forward, up) where forward=north, up=elevation
        centered = {}
        for gml_id, geo_data in all_geometries.items():
            centered_polygons = []
            for polygon in geo_data['polygons']:
                # Simply center - coordinates are already in the correct orientation
                # CityGML Y (north) = forward, Z (elevation) = up
                centered_poly = [(x - center[0], y - center[1], z - center[2]) 
                                for x, y, z in polygon]
                centered_polygons.append(centered_poly)
            
            centered[gml_id] = {
                'element_type': geo_data['element_type'],
                'polygons': centered_polygons,
                'metadata': geo_data['metadata']
            }
        
        return centered, self.offset
    
    def triangulate_polygon(self, vertices: List[Tuple[float, float, float]]) -> List[List[int]]:
        """
        Triangulate a polygon using simple fan triangulation.
        
        Args:
            vertices: List of vertex coordinates
            
        Returns:
            List of triangle indices (0-based)
        """
        n = len(vertices)
        
        # Remove duplicate last vertex if polygon is closed
        if n > 1 and vertices[0] == vertices[-1]:
            vertices = vertices[:-1]
            n = len(vertices)
        
        if n < 3:
            return []
        
        # Simple fan triangulation from first vertex
        triangles = []
        for i in range(1, n - 1):
            triangles.append([0, i, i + 1])
        
        return triangles
    
    def calculate_normal(self, v0: Tuple[float, float, float],
                        v1: Tuple[float, float, float],
                        v2: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """
        Calculate face normal using cross product.
        
        Args:
            v0, v1, v2: Triangle vertices
            
        Returns:
            Normalized normal vector (nx, ny, nz)
        """
        # Convert to numpy arrays
        p0 = np.array(v0)
        p1 = np.array(v1)
        p2 = np.array(v2)
        
        # Calculate edge vectors
        edge1 = p1 - p0
        edge2 = p2 - p0
        
        # Cross product
        normal = np.cross(edge1, edge2)
        
        # Normalize
        length = np.linalg.norm(normal)
        if length > 0:
            normal = normal / length
        
        return tuple(normal)
    
    def get_material_for_type(self, element_type: str) -> str:
        """
        Get material name based on element type.
        
        Args:
            element_type: e.g., 'RoofSurface', 'WallSurface'
            
        Returns:
            Material name
        """
        material_map = {
            'RoofSurface': 'roof',
            'WallSurface': 'wall',
            'GroundSurface': 'ground',
            'ClosureSurface': 'closure',
            'Building': 'building'
        }
        
        return material_map.get(element_type, 'default')
