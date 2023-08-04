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
from osm2geojson import json2geojson

from helpers import Usage, find_next_city, get_city_id, get_logger

logger = get_logger()


def get_boundaries(city_list):
    logger.info(f" City list: {', '.join(city_list)}")
    for city in city_list:
        logger.info(f" City:      {city}")
        city_id = get_city_id(city)

        # id = city['id']
        # admin_level = city['admin_level']

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
        logger.debug("Making requests for most granular admin_level")
        for admin_level in reversed(range(11)):
            r = requests.get(
                url, params={"data": query.format(admin_level=admin_level)}
            )
            if r.json()["elements"]:
                logger.debug(f"admin_level={admin_level}")
                found_boundaries = True
                break

        if not found_boundaries:
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
        logger.info(f" Saved: {out_file}")


def main():
    # Choose city
    cities_file = "cities_europe.txt"
    with open(cities_file) as f:
        cities_list = [city.strip() for city in f.readlines()]

    if len(sys.argv) > 3:
        raise Usage("Too many arguments")
    if len(sys.argv) == 3:
        if sys.argv[1] == "start":
            start_loc = cities_list.index(sys.argv[2])
            city_list = cities_list[start_loc:]
        else:
            raise Usage("Invalid argument")
    elif len(sys.argv) == 2:
        city_list = [sys.argv[1]]
    else:
        # Choose City
        # city_list = cities_list[8:14]
        city_list = [cities_list[14]]

    get_boundaries(city_list)

    if len(city_list) == 1:
        next_city = find_next_city(cities_list, city_list[0])
        logger.info(f" Next: {next_city}")


if __name__ == "__main__":
    main()
