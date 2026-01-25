# CityGML to 3D Converter

A simple,clean Python tool to convert CityGML files to OBJ format. Each `gml:id` becomes a separate group in the output 3D model.

## Features

- ✅ Parses CityGML 2.0 files
- ✅ Extracts all geometry by `gml:id`
- ✅ Exports to OBJ format with groups
- ✅ Automatic coordinate centering
- ✅ Material differentiation (roofs, walls, etc.)
- ✅ Metadata export (JSON)
- ✅ Web viewer included

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Conversion

```bash
cd src
python convert.py -i ../data/AI_27_D.gml -o ../output/citymodel.obj
```

### Count Objects Only

```bash
python convert.py -i ../data/AI_27_D.gml -o output.obj --count-only
```

### View in Browser

1. Convert your CityGML file to OBJ
2. Copy the generated files to the same directory as `viewer.html`:
   - `citymodel.obj`
   - `citymodel.mtl`
3. Start a local web server:
   ```bash
   cd /Users/mal/Desktop/gml-view/output
   python -m http.server 8000
   ```
4. Open `http://localhost:8000/../viewer.html` in your browser

## Output Structure

```
output/
├── citymodel.obj           # 3D geometry
├── citymodel.mtl           # Materials
└── citymodel_metadata.json # Metadata (gml:ids, counts, offset)
```

### OBJ File Structure

The OBJ file contains:
- One group (`g`) per `gml:id`
- Triangulated geometry with normals
- Material assignments based on element type

Example:
```obj
g AI_27_D_711214_9324255-roof
usemtl building
v -29.819709 -40.965589 -23.624195
...
```

## Architecture

- **`parser.py`** - CityGML XML parsing using lxml
- **`geometry.py`** - Coordinate transformations and triangulation
- **`obj_writer.py`** - OBJ/MTL file generation
- **`convert.py`** - CLI interface

## Coordinate System

- Input: Large UTM coordinates (EPSG:32748)
- Processing: Automatically centered to origin
- Original offset saved in `metadata.json`

## Materials

Automatic color assignment:
- 🔴 **Roofs** - Red/terracotta
- ⚪ **Walls** - Light gray
- 🟤 **Ground** - Brown
- 🔵 **Closure** - Blue

## Example Output

From `AI_27_D.gml`:
- **444 objects** (298 roofs + 144 walls + 2 buildings)
- **13.6 MB** OBJ file
- **381,948 lines** of geometry data

## Troubleshooting

**Import errors:**
```bash
cd src
python convert.py ...
```

**Large files:**
- The converter handles large files efficiently
- Uses streaming for memory efficiency

## License

MIT
