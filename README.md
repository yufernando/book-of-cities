# CityForm
*Urban form analysis and visualization*

CityForm is a Python tool for analyzing and visualizing urban form metrics for cities worldwide. It retrieves city boundaries, extracts building and street networks from OpenStreetMap, calculates comprehensive morphometric statistics, and generates GIS visualizations.

## Features

- Automated boundary retrieval from OpenStreetMap or US Census data
- Building and street network extraction from OpenStreetMap
- Urban morphometrics calculation (fractal dimension, entropy, connectivity, and more)
- GIS visualization generation in QGIS
- Batch processing support for multiple cities
- CSV export for aggregated analysis

## Table of Contents

- [Installation](#installation)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Docker](#docker)
- [Additional Operations](#additional-operations)
- [Tests](#tests)
- [Notes](#notes)
- [Sources](#sources)

---

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd cityform
```

2. Install Python dependencies:
```bash
pip install geopandas osmnx networkx pandas numpy momepy requests osm2geojson
```

3. (Optional) Set up Docker (see [Docker](#docker) section)

4. Configure paths in `config.py` or set environment variables if needed (see [Configuration](#configuration) section)

---

## Prerequisites

### Required

- **Python 3.x**
- **QGIS** (for visualization step)

### Optional

- **Docker** (recommended for consistent environment)

### Python Dependencies

- `geopandas` - Geospatial data operations
- `osmnx` - OpenStreetMap network extraction
- `networkx` - Network analysis
- `pandas` - Data manipulation
- `numpy` - Numerical computing
- `momepy` - Urban morphometrics analysis
- `requests` - HTTP requests
- `osm2geojson` - OSM to GeoJSON conversion

Install all dependencies:
```bash
pip install geopandas osmnx networkx pandas numpy momepy requests osm2geojson
```

---

## Configuration

### Path Configuration

Paths default to relative directories within the project. You can override them using environment variables:

- **`CITYFORM_PROJECT_ROOT`**: Project root directory (default: parent of `config.py` directory)
- **`CITYFORM_DATA_ROOT`**: Root data directory (default: `{PROJECT_ROOT}/data`)
- **`CITYFORM_DRIVE_ROOT`**: Drive/Research folder for QGIS outputs (default: `{PROJECT_ROOT}/../drive`)
- **`CITYFORM_QGIS_RESEARCH_SUBPATH`**: Subpath within drive folder (default: `"Research/City Science - Global City Profiles"`)

**Example**: To customize the data directory:
```bash
export CITYFORM_DATA_ROOT=/path/to/custom/data
```

### Runtime Configuration

Edit `config.py` to configure:

- **`CITY_FILE`**: Path to file containing city list (e.g., `"data/cities_us.txt"`)
- **`STREETS`**: Enable/disable street extraction (default: `True`)
- **`BUILDINGS`**: Enable/disable building extraction (default: `True`)
- **`MORPHOMETRICS`**: Enable/disable morphometrics calculation (default: `True`)
- **`FULL_VARIABLES`**: Calculate full set of variables vs. basic set (default: `True`)
- **`CSV_OUT`**: Concatenate outputs to CSV (default: `False`)
- **`LOG_LEVEL`**: Logging level - `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"` (default: `"DEBUG"`)

---

## Project Structure

The project uses a structured data directory layout:

```
cityform/
├── data/
│   ├── 0_boundaries/          # City boundary files (.gpkg)
│   │   ├── 0_Census/          # US Census tract data (for US cities)
│   │   └── [city]/            # City-specific boundary files
│   ├── 1_buildings_streets/   # Building and street network files
│   ├── 2_morphometrics/       # Calculated morphometric statistics
│   ├── 4_csv/                 # Concatenated CSV outputs
│   └── cities_*.txt           # City list files by region
├── boundaries/                # Boundary retrieval modules
├── layers/                    # Building/street extraction and morphometrics
├── QGIS/                      # QGIS visualization scripts
├── notebooks/                 # Jupyter notebooks for analysis
├── config.py                  # Configuration and path settings
└── run.py                     # Main entry point
```

**Note**: By default, all data directories are relative to the project root. Paths can be customized using environment variables (see [Configuration](#configuration) section).

For QGIS outputs, the default path assumes a `drive/` folder at the same level as the project root. This can be overridden using the `CITYFORM_DRIVE_ROOT` environment variable.

---

## Usage

### Workflow Overview

For a given city, perform the following steps:

### 1. Get Boundaries

**For US cities:**
- Use census tracts for more accurate boundaries
- Open QGIS and load census tracts of state from `data/0_boundaries/0_Census`
- Select and save polygons for the city into a geopackage in `data/0_boundaries/[city]/[city].gpkg`

**For non-US cities:**
- Get boundaries from OpenStreetMap (OSM)
- Add a list of cities into a text file (e.g., `data/cities_europe.txt`) and set the filepath in `config.py`
- Run: `python run.py boundaries`
- If the script fails to retrieve boundaries, download them directly from [Overpass Turbo](https://overpass-turbo.eu) and save them into `data/0_boundaries/[city]/[city].gpkg`

**Note**: If you use QGIS to edit the boundaries, save the QGIS file into `data/3_QGIS/[city].qgz` for step 3.

### 2. Get Buildings, Streets and Morphometrics

Edit `config.py` to specify which cities to process and which features to extract:

- **Buildings**: Building footprints from OpenStreetMap
- **Streets**: Street network graphs from OpenStreetMap  
- **Morphometrics**: Urban form metrics including:
  - **Scale complexity**: Fractal dimension, compactness (area), diameter-periphery
  - **Spatial complexity & connectivity**: Shannon entropy (street orientation), average street length, betweenness centrality, streets per node, intersection density, street density, circuity, node connectivity, PageRank, closeness centrality (local & global), straightness centrality
  - **Built complexity/morphology**: Building area, building compactness, tessellation area, building orientation, building alignment, street alignment, street profile metrics (width, heights, openness)
  - **Infrastructure**: Total area, total built area, total street length

Run the script with `python run.py` or any option described in the [Docker](#docker) section below. The output will be stored in `data/1_buildings_streets` and `data/2_morphometrics`.

### 3. Visualize in QGIS

1. Load the boundaries from `data/0_boundaries/[city]/[city].gpkg` into QGIS
2. Add a `Dark Matter (retina)` basemap layer
3. Save the file as `data/3_QGIS/[city].qgz` if it does not exist
4. In the QGIS Python Editor, run `QGIS/0_load_layers.py`
5. Reclassify all layers: for each morphometrics layer, go to **Properties > Symbology** and click **Delete All**, then **Classify**
6. Open map layout and check it looks good, set scale to round numbers
7. In the QGIS Python Editor, run `QGIS/1_export_images.py`

All images are exported to the QGIS figures directory (default: `{DRIVE_ROOT}/{QGIS_RESEARCH_SUBPATH}/figs/[city]/[city].jpg`).

To change the output location, set the `CITYFORM_DRIVE_ROOT` and/or `CITYFORM_QGIS_RESEARCH_SUBPATH` environment variables.

### Command Line Arguments

You can use command line arguments directly to run a list of cities:
```bash
python run.py "New York" "Los Angeles"
```

You can also provide a text file and a starting point:
```bash
python run.py data/cities_us.txt start "New York"
```

This will process all cities in the file starting from "New York".

---

## Docker

### Run the container

To use a Docker image with all required packages:
```bash
make docker
```

This will:
- Start a JupyterLab container with all dependencies pre-installed
- Mount the project directory to `/home/jovyan/work/cityform`
- Open JupyterLab in Chrome (Mac OS specific - modify Makefile for other platforms)

**Note**: The `make docker` command includes platform-specific code for opening Chrome on macOS. Modify the Makefile if you're on a different platform.

### Run inside the container

To open a shell inside the container:
```bash
make shell
```

Then edit `config.py` and run:
```bash
python run.py
```

### Run outside the container

To run commands from outside the container:
```bash
make run
make run cmd="'Buenos Aires'"
make run cmd="data/cities_us.txt start 'New York'"
```

---

## Additional Operations

### Concatenate Morphometrics

To combine all morphometric files into a single CSV for analysis:
```bash
python concatenate.py
```

Or using the Makefile:
```bash
make concatenate
```

This will create `data/4_csv/Morphometrics.csv` with all cities combined. The script will prompt for confirmation before overwriting an existing CSV.

---

## Tests

Run the test suite:
```bash
pytest
```

Run tests for specific modules:
```bash
pytest layers/tests/
```

---

## Notes

- **US cities**: Census tract boundaries are preferred over OSM boundaries for more accurate results
- **Large cities**: May timeout when fetching boundaries from Overpass API. In such cases, download boundaries manually from [Overpass Turbo](https://overpass-turbo.eu)
- **Boundary retrieval failures**: If automated boundary retrieval fails, download the GeoJSON manually from Overpass Turbo and save as `data/0_boundaries/[city]/[city].gpkg`
- **QGIS installation**: The QGIS visualization step requires QGIS to be installed separately on your system
- **Processing time**: Large cities with many polygons may take significant time to process, especially for full morphometrics calculation
- **Data sources**: All building and street data is sourced from OpenStreetMap, which may have varying completeness depending on the city

---

## Sources

- **US Census Data**: [Census TIGER/Line Shapefiles](https://www2.census.gov/geo/tiger/TIGER_RD18/STATE/)
- **OpenStreetMap**: [Overpass API](http://overpass-api.de/api/interpreter) and [Overpass Turbo](https://overpass-turbo.eu)
- **New York City Boroughs**: [NYC Open Data Portal](https://data.cityofnewyork.us/City-Government/Borough-Boundaries/tqmj-j8zm)
