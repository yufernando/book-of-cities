"""Configuration variables"""

import os
from pathlib import Path

from layers.helpers import parse_user_input, read_cities_from_file

# ============================================================================
# Path Configuration
# ============================================================================
# Project root (one level up from code/)
PROJECT_ROOT = Path(
    os.environ.get(
        "BOC_PROJECT_ROOT",
        Path(__file__).resolve().parent.parent,
    )
)

# Data directories
DATA_ROOT = Path(os.environ.get("BOC_DATA_ROOT", PROJECT_ROOT / "data"))

# Drive/Research folder (for QGIS outputs)
# Default assumes drive folder is at same level as project root
DRIVE_ROOT = Path(
    os.environ.get(
        "BOC_DRIVE_ROOT",
        PROJECT_ROOT.parent / "drive",
    )
)

# QGIS-specific paths
# These can be overridden via environment variables if the structure differs
QGIS_RESEARCH_SUBPATH = os.environ.get(
    "BOC_QGIS_RESEARCH_SUBPATH", "Research/City Science - Global City Profiles"
)
QGIS_DATA_ROOT = DRIVE_ROOT / QGIS_RESEARCH_SUBPATH / "data"
QGIS_FIGS_ROOT = DRIVE_ROOT / QGIS_RESEARCH_SUBPATH / "figs"

# Specific data subdirectories (for convenience)
BOUNDARIES_DIR = DATA_ROOT / "0_boundaries"
BUILDINGS_STREETS_DIR = DATA_ROOT / "1_buildings_streets"
MORPHOMETRICS_DIR = DATA_ROOT / "2_morphometrics"
CSV_DIR = DATA_ROOT / "4_csv"

# ============================================================================
# Runtime Configuration
# ============================================================================

# CITY_FILE = "data/cities_us.txt"
# CITY_FILE = "data/cities_europe.txt"
# CITY_FILE = "data/cities_southamerica.txt"
# CITY_FILE = "data/cities_asia.txt"
# CITY_FILE = "data/cities_mena.txt"
# CITY_FILE = "data/cities_oceania.txt"
CITY_FILE = "data/cities_barcelona.txt"
STREETS = True
BUILDINGS = True
MORPHOMETRICS = True
FULL_VARIABLES = True
CSV_OUT = False  # concatenate all morphometrics files into one CSV
# LOG_LEVEL = "INFO"
LOG_LEVEL = "DEBUG"

if parse_user_input() is not None:
    CITY_LIST = parse_user_input()
else:
    CITY_LIST = read_cities_from_file(CITY_FILE)
