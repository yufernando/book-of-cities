"""
Get boundaries from OSM
"""
# Import packages
import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from osm2geojson import json2geojson

from layers.helpers import get_city_id

logger = logging.getLogger("log")


def save_query_data(city, column, value, filepath):
    """Save admin_level or city_id to query data spreadsheet"""
    try:
        df = pd.read_csv(filepath, dtype={"city": str, column: "Int64"})
        if city in df["city"].unique():
            df.loc[df["city"] == city, column] = value
            out_df = df.copy()
            logger.debug("Updating %s=%s in %s", column, value, filepath)
            logger.debug(out_df)
        else:
            out_dict = {"city": city, column: value}
            out_df = pd.DataFrame([out_dict])
            out_df = pd.concat([df, out_df])
            logger.debug("Appending new data to %s", filepath)
            logger.debug(out_df)
    except FileNotFoundError:
        pass

    out_df.to_csv(filepath, index=False)


def get_query_settings_from_file(city, filepath):
    city_id = None
    admin_level = None
    try:
        logger.debug("Reading: %s", filepath)
        df = pd.read_csv(filepath)
        df_city = df.loc[df["city"] == city]
        if not df_city.empty:
            city_id = df.loc[df["city"] == city, "city_id"].values[0]
            logger.debug("Read city_id: %s", city_id)
            admin_level = df.loc[df["city"] == city, "admin_level"].values[0]
            logger.debug("Read admin_level: %s", admin_level)
    except FileNotFoundError:
        pass
    except KeyError:
        pass
    return city_id, admin_level


QUERY = """
[out:json][timeout:25];
// fetch area to search in
area(id:{city_id})->.searchArea;
(
//node["admin_level"="{admin_level}"](area.searchArea);
//way["admin_level"="{admin_level}"](area.searchArea);
relation["admin_level"="{admin_level}"](area.searchArea);
);
out body;
>;
out skel qt;
"""


def make_request(city_id, admin_level):
    headers = {"User-Agent": "Book-of-Cities/0.1"}
    url = "http://overpass-api.de/api/interpreter"  # Overpass API URL
    r = requests.get(
        url,
        params={"data": QUERY.format(city_id=city_id, admin_level=admin_level)},
        timeout=30,
        headers=headers,
    )
    if not r.ok:
        logger.debug(
            "city_id=%s, admin_level=%s, status_code=%s",
            city_id,
            admin_level,
            r.status_code,
        )
        print("QUERY:")
        print(QUERY.format(city_id=city_id, admin_level=admin_level))
        return None
    return r.json()


def get_admin_level(city_id):
    for admin_level in reversed(range(11)):
        geojson = make_request(city_id, admin_level)
        if geojson and geojson["elements"]:
            logger.debug("admin_level=%s", admin_level)
            break
    else:
        return None, None

    return admin_level, geojson


def get_boundaries(city_list):
    """Get boundaries"""
    city_list_names_only = [city.split(":")[0] for city in city_list]
    logger.info("City list: %s", ", ".join(city_list_names_only))

    for city in city_list:
        if ":" in city:
            city, explanation = city.split(":", 1)
            logger.info("City:      %s (SKIPPED: %s)", city, explanation.strip())
            continue

        logger.info("City:      %s", city)

        # Get city_id and admin_level from file
        city_id, admin_level = get_query_settings_from_file(city, "data/query_data.csv")

        # Get city id from Nominatim
        if pd.isna(city_id):
            try:
                logger.debug("city_id not found. Geolocating city: %s", city)
                city_id = get_city_id(city)
                save_query_data(city, "city_id", city_id, "data/query_data.csv")
            except ValueError:
                logger.error("Could not geolocate city: %s", city)
                continue

        # Get boundaries from Overpass API
        if pd.isna(admin_level):
            logger.debug(
                "admin_level not found. Making requests to for most granular admin_level."
            )
            admin_level, geojson = get_admin_level(city_id)
            # Save admin_level
            save_query_data(city, "admin_level", admin_level, "data/query_data.csv")
            if not geojson:
                logger.error("No boundaries found for city: %s", city)
                continue
        else:
            logger.debug("admin_level found: %s. Sending request", admin_level)
            geojson = make_request(city_id, admin_level)

        # Create GeoDataFrame
        try:
            geojson = json2geojson(geojson)
        except TypeError:
            logger.error(
                "There was an error parsing the geojson for city: %s. Please download geojson from https://overpass-turbo.eu",
                city,
            )
            continue

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
        logger.info("Saved: %s", out_file)
