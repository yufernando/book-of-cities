"""
Helper functions for the command line interface.
"""
# import warnings

import logging
import sys
from pathlib import Path

from geopy.geocoders import Nominatim

# warnings.filterwarnings("ignore")

logger = logging.getLogger("log")


def format_time(time_elapsed):
    """Takes seconds and returns hours, minutes and seconds"""
    hours = int(time_elapsed // 3600)
    minutes = int((time_elapsed % 3600) // 60)
    seconds = int(time_elapsed % 60)
    return f"{hours}h {minutes}m {seconds}s"


def find_next_city(city_list, mystring):
    """Find the next city in the city_list"""
    try:
        # Find the index of mystring in the city_list
        index = city_list.index(mystring)

        # Check if mystring is the last element in the city_list
        if index == len(city_list) - 1:
            return None  # No next city available

        # Return the next city in the city_list
        return city_list[index + 1]
    except ValueError:
        return None  # mystring not found in the city_list


def load_cities_from_file(filename):
    """Load cities from a text file"""
    with open(filename, "r", encoding="utf-8") as file:
        cities = [city.strip() for city in file.readlines()]
    return cities


def get_city_id(city_name):
    """Get the city ID from the city name"""
    geolocator = Nominatim(user_agent="get-city-id")
    geo_results = geolocator.geocode(city_name, exactly_one=False, limit=3)
    if not geo_results:
        raise ValueError(f"Could not geolocate city: {city_name}")

    city = None
    for result in geo_results:
        if result.raw.get("osm_type") == "relation":
            city = result
            break

    if not city:
        raise ValueError(
            f"No results of type 'relation' found after geolocating city: {city_name}"
        )

    area_id = int(city.raw.get("osm_id")) + 3600000000
    return area_id


HELP_MESSAGE = """
Usage: python run.py [cities.txt] [start] city1 city2 city3 ...

Arguments:
cities.txt: A text file containing a list of cities.
start: If set, will run the list starting from the provided city.
city1 city2 city3 ...: A list of cities to run.
"""


def parse_user_input() -> list[str]:
    """Wrapper for parse_input using arguments provided by the user."""
    return parse_input(sys.argv)


def read_cities_from_file(filepath: str) -> list[str]:
    """Read cities from a text file."""
    with open(filepath, encoding="utf-8") as f:
        return [city.strip().split(":")[0].split(",")[0] for city in f.readlines()]


def parse_input(argv: list[str]) -> list[str]:
    """Parse user input and get city list."""
    # No arguments provided
    if len(argv) == 1:
        logger.debug("No arguments provided.")
        city_list = None

    # If first argument is a file, load cities from file
    elif Path(argv[1]).suffix == ".txt":
        if Path(argv[1]).is_file():
            city_list = read_cities_from_file(argv[1])
            if len(argv) > 2:
                if argv[2] == "start":
                    if len(argv) == 3:
                        raise IndexError("No city provided.\n" + HELP_MESSAGE)
                    if len(argv) > 4:
                        raise IndexError("Too many arguments.\n" + HELP_MESSAGE)
                    start_loc = city_list.index(argv[3])
                    city_list = city_list[start_loc:]
                else:
                    city_list = argv[2:]
        else:
            raise FileNotFoundError(
                f"Cities file {Path(argv[1])} not found.\n" + HELP_MESSAGE
            )
    else:
        # If arguments are city names, run those cities
        city_list = argv[1:]

    return city_list
