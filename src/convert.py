#!/usr/bin/env python3
"""
CityGML to OBJ Converter

Simple, clean converter for CityGML to Wavefront OBJ format.
Each gml:id becomes a separate group in the OBJ file.
"""

import argparse
import os
import sys
import logging
from parser import CityGMLParser
from geometry import GeometryProcessor
from obj_writer import OBJWriter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Convert CityGML to OBJ format with groups per gml:id'
    )
    
    parser.add_argument(
        '-i', '--input',
        required=True,
        help='Input CityGML file path'
    )
    
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output OBJ file path'
    )
    
    parser.add_argument(
        '--count-only',
        action='store_true',
        help='Only count gml:ids, do not convert'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    try:
        # Parse CityGML
        logger.info("=" * 60)
        logger.info("CityGML to OBJ Conversion")
        logger.info("=" * 60)
        
        citygml_parser = CityGMLParser(args.input)
        geometries = citygml_parser.parse()
        
        if args.count_only:
            logger.info(f"\nTotal gml:ids with geometry: {len(geometries)}")
            for gml_id, geo_data in geometries.items():
                poly_count = len(geo_data['polygons'])
                logger.info(f"  {gml_id}: {poly_count} polygons ({geo_data['element_type']})")
            return
        
        if not geometries:
            logger.warning("No geometry found in CityGML file")
            sys.exit(0)
        
        # Process geometry
        logger.info("\nProcessing geometry...")
        geo_processor = GeometryProcessor()
        centered_geometries, offset = geo_processor.center_coordinates(geometries)
        
        # Write OBJ
        logger.info("\nWriting OBJ file...")
        obj_writer = OBJWriter(geo_processor)
        obj_writer.write_single_obj(centered_geometries, args.output, offset)
        
        logger.info("\n" + "=" * 60)
        logger.info("Conversion completed successfully!")
        logger.info(f"Output: {args.output}")
        logger.info(f"Total objects: {len(geometries)}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Conversion failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
