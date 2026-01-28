#!/bin/bash
# Start server script with conda environment

echo "Starting CityGML Conversion Server..."
echo ""

# Activate conda environment and start server
eval "$(conda shell.bash hook)"
conda activate citygml-view
python server.py
