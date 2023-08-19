"""
Helper functions for the command line interface.
"""
# import warnings

from pathlib import Path

from geopy.geocoders import Nominatim

# warnings.filterwarnings("ignore")


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


class Usage(Exception):
    pass


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
Usage: python {} [cities.txt] [start] city1 city2 city3 ...

Arguments:
cities.txt: A text file containing a list of cities.
start: If set, will run the list starting from the provided city.
city1 city2 city3 ...: A list of cities to run.
"""


def parse_user_input(argv):
    """Parse user input and get city list."""
    if len(argv) == 1:
        raise Usage(
            "Must provide arguments.\n" + HELP_MESSAGE.format(Path(__file__).name)
        )

    city_file_provided = False

    if Path(argv[1]).is_file():  # first argument is "cities.txt"
        city_file_provided = True
        with open(argv[1], encoding="utf-8") as f:
            cities_list = [
                city.strip().split(":")[0].split(",")[0] for city in f.readlines()
            ]
        argv = argv[1:]  # remove "cities.txt" from argv

    if len(argv) == 1:
        city_list = cities_list
    elif argv[1] == "start":
        if not city_file_provided:
            raise Usage(
                "Must provide a list of cities in a text file.\n"
                + HELP_MESSAGE.format(Path(__file__).name)
            )
        if len(argv) > 3:
            raise Usage(
                "Too many arguments.\n" + HELP_MESSAGE.format(Path(__file__).name)
            )
        start_loc = cities_list.index(argv[2])
        city_list = cities_list[start_loc:]
    else:
        city_list = argv[1:]
        cities_list = city_list

    return city_list, cities_list, city_file_provided
