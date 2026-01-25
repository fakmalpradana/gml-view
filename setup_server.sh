#!/bin/bash
# Setup script for CityGML Conversion Server

echo "Setting up CityGML Conversion Server with conda environment..."

# Activate conda environment
eval "$(conda shell.bash hook)"
conda activate citygml-view

# Install dependencies
pip install flask flask-cors

echo ""
echo "Setup complete!"
echo ""
echo "To run the server:"
echo "  1. Activate conda environment: conda activate citygml-view"
echo "  2. Run server: python3 server.py"
echo ""
echo "To deactivate when done: conda deactivate"
