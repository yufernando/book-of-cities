"""
Helper functions
"""
import logging
import math
import sys
import warnings
from pathlib import Path

import numpy as np
import osmnx as ox
import pandas as pd
from geopy.geocoders import Nominatim

warnings.filterwarnings("ignore")

logger = logging.getLogger("log." + __name__)


def reverse_bearing(x):
    return x + 180 if x < 180 else x - 180


def get_bearings(G, ID):
    # calculate the edge bearings
    Gu = ox.add_edge_bearings(ox.get_undirected(G))

    weight_by_length = False

    bearings = {}
    if weight_by_length:
        # weight bearings by length (meters)
        city_bearings = []
        for u, v, k, d in Gu.edges(keys=True, data=True):
            city_bearings.extend([d["bearing"]] * int(d["length"]))
        b = pd.Series(city_bearings)
        bearings[ID] = pd.concat([b, b.map(reverse_bearing)]).reset_index(drop="True")
    else:
        # don't weight bearings, just take one value per street segment
        b = pd.Series([d["bearing"] for u, v, k, d in Gu.edges(keys=True, data=True)])
        bearings[ID] = pd.concat([b, b.map(reverse_bearing)]).reset_index(drop="True")
    return bearings[ID]


def count_and_merge(n, bearings):
    # make twice as many bins as desired, then merge them in pairs
    # prevents bin-edge effects around common values like 0° and 90°
    n = n * 2
    bins = np.arange(n + 1) * 360 / n
    count, _ = np.histogram(bearings, bins=bins)

    # move the last bin to the front, so eg 0.01° and 359.99° will be binned together
    count = np.roll(count, 1)
    return count[::2] + count[1::2]


def get_orientation_order(count):
    try:
        H0 = 0
        for i in range(len(count)):
            Pi = count[i] / sum(count)
            if Pi != 0:
                H0 += Pi * np.log(Pi)

        H0 = -1 * H0
        Hmax = np.log(len(count))
        Hg = np.log(2)

        orientation_order = 1 - (((H0 - Hg) / (Hmax - Hg)) ** 2)

    except Exception as e:
        print(f"Error in orientation order {e}")

    return orientation_order


def pp_compactness(geom):  # Polsby-Popper
    """Calculate compactness"""
    p = geom.length
    a = geom.area
    return (4 * math.pi * a) / (p * p)


def fractal_dimension(Z, threshold=0.8):
    """Returns box-counting dimension of a 2D array.
    Args:
        Z: 2D array to be analysed.
        threshold: Cutoff for converting values in Z to 1 and 0.
    Returns:
        The estimated box counting dimension.
    """
    # Only for 2d image
    assert len(Z.shape) == 2

    def boxcount(Z, k):
        S = np.add.reduceat(
            np.add.reduceat(Z, np.arange(0, Z.shape[0], k), axis=0),
            np.arange(0, Z.shape[1], k),
            axis=1,
        )
        # We count non-empty (0) and non-full boxes (k*k)
        return len(np.where((S > 0) & (S < k * k))[0])

    # Transform Z into a binary array
    Z = Z < threshold
    # Minimal dimension of image
    p = min(Z.shape)
    # Greatest power of 2 less than or equal to p
    n = 2 ** np.floor(np.log(p) / np.log(2))
    # Extract the exponent
    n = int(np.log(n) / np.log(2))
    # Build successive box sizes (from 2**n down to 2**1)
    sizes = 2 ** np.arange(n, 1, -1)
    # Actual box counting with decreasing size
    counts = []
    for size in sizes:
        counts.append(boxcount(Z, size))
    # Fit the successive log(sizes) with log (counts)
    coeffs = np.polyfit(np.log(sizes), np.log(counts), 1)
    return -coeffs[0]


def clean_heights(x):
    """Cleans building heights"""
    try:
        return float(x)
    except ValueError:
        return 0


def format_time(time_elapsed):
    """Takes seconds and returns hours, minutes and seconds"""
    hours = int(time_elapsed // 3600)
    minutes = int((time_elapsed % 3600) // 60)
    seconds = int(time_elapsed % 60)
    return f"{hours}h {minutes}m {seconds}s"


def find_next_city(city_list, mystring):
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
    with open(filename, "r") as file:
        cities = [city.strip() for city in file.readlines()]
    return cities


class Usage(Exception):
    pass


class TooManyPolygons(Exception):
    pass


def get_city_id(city_name):
    geolocator = Nominatim(user_agent="get-city-id")
    geo_results = geolocator.geocode(city_name, exactly_one=False, limit=3)
    if not geo_results:
        raise ValueError(f"Could not geolocate city: {city_name}")

    city = None
    for r in geo_results:
        if r.raw.get("osm_type") == "relation":
            city = r
            break

    if not city:
        raise ValueError(
            f"No results of type 'relation' found after geolocating city: {city_name}"
        )

    area_id = int(city.raw.get("osm_id")) + 3600000000
    return area_id


def get_logger(filename=None):
    if not filename:
        filename = Path(sys.argv[0]).stem + ".log"

    # Configure logging
    logger = logging.getLogger("log")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    fh = logging.FileHandler(filename, mode="w")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    logger.info(f" Saving logs to {filename}")
    return logger


help_message = """
Usage: python {} [cities.txt] [start] city1 city2 city3 ...

Arguments:
cities.txt: A text file containing a list of cities.
start: If set, will run the list starting from the provided city.
city1 city2 city3 ...: A list of cities to run.
"""
