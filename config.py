"""Configuration variables"""
from layers.helpers import parse_user_input, read_cities_from_file

# CITY_FILE = "data/cities_us.txt"
CITY_FILE = "data/cities_europe.txt"
STREETS = False
BUILDINGS = False
MORPHOMETRICS = True
FULL_VARIABLES = True
CSV_OUT = False
LOG_LEVEL = "INFO"

CITY_LIST = (
    parse_user_input()
    if parse_user_input() is not None
    else read_cities_from_file(CITY_FILE)
)
