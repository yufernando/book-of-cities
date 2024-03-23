"""Configuration variables"""

from layers.helpers import parse_user_input, read_cities_from_file

# CITY_FILE = "data/cities_us.txt"
# CITY_FILE = "data/cities_europe.txt"
# CITY_FILE = "data/cities_southamerica.txt"
CITY_FILE = "data/cities_asia.txt"
# CITY_FILE = "data/cities_mena.txt"
# CITY_FILE = "data/cities_oceania.txt"
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
