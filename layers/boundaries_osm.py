"""
Get boundaries from OSM
"""
import logging
import sys
from pathlib import Path

import geopandas as gpd
import osmnx as ox

# Import packages
import pandas as pd
import requests
from morpho.helpers import HELP_MESSAGE, Usage, find_next_city, get_city_id
from osm2geojson import json2geojson

logger = logging.getLogger("log")


def get_boundaries(city_list):
    city_list_names_only = [city.split(":")[0] for city in city_list]
    logger.info(f"City list: {', '.join(city_list_names_only)}")
    for city in city_list:
        if ":" in city:
            city, explanation = city.split(":", 1)
            logger.info(f"City:      {city} (SKIPPED: {explanation.strip()})")
            continue

        logger.info(f"City:      {city}")
        try:
            city_id = get_city_id(city)
        except ValueError:
            logger.error(f"Could not geolocate city: {city}")
            continue

        # Create query
        # Get city id from Nominatim
        query = f"""
        [out:json][timeout:25];
        // fetch area to search in
        area(id:{city_id})->.searchArea;
        (
        //node["admin_level"="{{admin_level}}"](area.searchArea);
        //way["admin_level"="{{admin_level}}"](area.searchArea);
        relation["admin_level"="{{admin_level}}"](area.searchArea);
        );
        out body;
        >;
        out skel qt;
        """

        # Make request
        url = "http://overpass-api.de/api/interpreter"  # Overpass API URL

        # Search for most granular admin_level
        logger.info("Making requests for most granular admin_level")
        for admin_level in reversed(range(11)):
            r = requests.get(
                url, params={"data": query.format(admin_level=admin_level)}
            )
            if r.json()["elements"]:
                logger.info(f"admin_level={admin_level}")
                break
        else:
            message = f"No boundaries found for city: {city}."
            logger.error(message)
            raise ValueError(message)

        # Save query data
        out_dict = {"city": city, "city_id": city_id, "admin_level": admin_level}
        out_df = pd.DataFrame([out_dict])

        try:
            df = pd.read_csv("query_data.csv")
            if city in df["city"].unique():
                df.loc[df["city"] == city, "city_id"] = city_id
                df.loc[df["city"] == city, "admin_level"] = admin_level
                out_df = df.copy()
            else:
                out_df = pd.concat([df, out_df])
        except FileNotFoundError:
            pass

        out_df.to_csv("query_data.csv", index=False)

        # Clean results
        geojson = json2geojson(r.json())
        gdf = gpd.GeoDataFrame().from_features(geojson)
        gdf = gdf.loc[gdf.geom_type == "MultiPolygon"]

        gdf = gdf.set_crs("epsg:4326")
        # gdf = gdf.loc[gdf['type'] == 'relation']

        if not all(gdf["type"] == "relation"):
            message = "Not all types are relations."
            logger.error(message)
            raise ValueError(message)

        # Save
        data_folder = Path("../data")
        out_city = city.split(",")[0]  # Fix "Saint Petersburg, Russia" and others
        out_file = data_folder / "0_boundaries" / out_city / (out_city + ".gpkg")
        if not out_file.parent.exists():
            out_file.parent.mkdir(parents=True)
        gdf.to_file(out_file, driver="GPKG")
        logger.info(f"Saved: {out_file}")


def main():
    if len(sys.argv) == 1:
        raise IndexError("Must provide arguments.\n" + HELP_MESSAGE)

    city_file_provided = False

    if Path(sys.argv[1]).is_file():  # first argument is "cities.txt"
        city_file_provided = True
        with open(sys.argv[1]) as f:
            cities_list = [city.strip() for city in f.readlines()]
        sys.argv = sys.argv[1:]  # remove "cities.txt" from sys.argv

    if sys.argv[1] == "start":
        if not city_file_provided:
            raise (
                "Must provide a list of cities in a text file.\n"
                + HELP_MESSAGE
            )
        if len(sys.argv) > 3:
            raise IndexError("Too many arguments.\n" + HELP_MESSAGE
        start_loc = cities_list.index(sys.argv[2])
        city_list = cities_list[start_loc:]
    else:
        city_list = sys.argv[1:]

    get_boundaries(city_list)

    if city_file_provided:
        next_city = find_next_city(cities_list, city_list[0])
        logger.info(f"Next: {next_city}")


if __name__ == "__main__":
    main()
