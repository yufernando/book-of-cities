#!/usr/bin/env python
# coding: utf-8
"""
Get Buildings and Streets and run Morphometrics
"""
import logging
import time

import geopandas as gpd
import osmnx as ox
import pandas as pd

import config
from layers.helpers import find_next_city, format_time
from layers.morpho import get_morphometrics

logger = logging.getLogger("log")


def get_polygons(city):
    """Get polygons from city."""
    input_file = config.BOUNDARIES_DIR / city / (city + ".gpkg")

    gdf = gpd.read_file(input_file, driver="GPKG")
    logger.info("Boundaries: Input %s (%s polygons)", input_file, len(gdf))
    # if len(gdf) > 300:
    #     raise ValueError(f"{city} boundaries file too large: {len(gdf)} polygons.")

    # Force gdf projection
    gdf = ox.project_gdf(gdf, to_crs="epsg:4326", to_latlong=False)

    # Create unique ID
    gdf = gdf.reset_index(drop=True)
    gdf["UID"] = gdf.index

    gdf["collapse"] = 0
    gdf = gdf[gdf.is_valid]
    try:
        gdf_collapsed = gdf.dissolve(by="collapse")
    except Exception as e:
        print(e)
        breakpoint()

    return gdf, gdf_collapsed


def get_buildings(gdf_collapsed):
    """Get buildings from city."""
    tags = {"building": True}
    logger.info("Buildings:  Downloading all buildings.")
    buildings = ox.features_from_polygon(gdf_collapsed["geometry"][0], tags)
    buildings = buildings[["geometry", "name"]]
    buildings_save = buildings.drop(labels="node", axis=0, level=0)

    # Keep only polygons
    is_polygon_mask = buildings_save["geometry"].apply(
        lambda geom: geom.geom_type == "Polygon"
    )
    buildings_save = buildings_save[is_polygon_mask]

    return buildings_save


def get_streets(gdf_collapsed):
    """Get streets from city."""
    # Get Streets
    logger.info("Streets:    Downloading all streets.")
    graph = ox.graph_from_polygon(
        gdf_collapsed["geometry"][0], network_type="drive", retain_all=True
    )

    # Remove nodes to export to geopackage
    gdf_streets = ox.utils_graph.graph_to_gdfs(graph, nodes=False)
    for column in gdf_streets.columns:
        gdf_streets[column] = gdf_streets[column].apply(
            lambda x: ", ".join(map(str, x)) if isinstance(x, list) else x
        )

    return gdf_streets


def get_city_layers(
    city, buildings=True, streets=True, morphometrics=True, save=True, full=True
):
    """Get city layers."""
    logger.info("-----------------------------------------------------------------")
    logger.info("City:       %s", city)
    start = time.perf_counter()

    gdf, gdf_collapsed = get_polygons(city)

    if streets:
        gdf_streets = get_streets(gdf_collapsed)
        if save:
            out_file = config.BUILDINGS_STREETS_DIR / (city + " - Streets.gpkg")
            if out_file.exists():
                out_file.unlink()
            gdf_streets.to_file(out_file, driver="GPKG")
            logger.info("Streets:    Saved %s", out_file)
    else:
        logger.info("Streets:    Skipped.")

    if buildings:
        gdf_buildings = get_buildings(gdf_collapsed)
        if save:
            # Save
            out_file = config.BUILDINGS_STREETS_DIR / (city + " - Buildings.gpkg")
            if out_file.exists():
                out_file.unlink()
            gdf_buildings.to_file(out_file, driver="GPKG")
            logger.info("Buildings:  Saved %s", out_file)
    else:
        logger.info("Buildings:  Skipped.")

    if morphometrics:
        gdf = get_morphometrics(gdf, full=full)
        if save:
            out_file = config.MORPHOMETRICS_DIR / (city + " - morpho.gpkg")
            gdf.to_file(out_file, driver="GPKG")
            logger.info("Morphometrics: Saved %s", out_file)
    else:
        logger.info("Morphometrics: Skipped.")

    end = time.perf_counter()
    logger.info("Done: %s. Time elapsed: %s", city, format_time(end - start))


def main(
    city_list, buildings=True, streets=True, morphometrics=True, full=True, csv_out=True
):
    """Entrypoint."""
    for city in city_list:
        try:
            get_city_layers(
                city, buildings, streets, morphometrics, full=full, save=True
            )
        except Exception as e:
            logger.exception(e)  # logger.exception adds traceback and nice error format
            logger.error("Error processing city %s. Skipping.", city)
            continue

    next_city = find_next_city(city_list, city)
    if next_city:
        logger.info("Next: %s", next_city)

    if csv_out:
        # Concatenate all files in the 2_morphometrics folder
        morpho_folder = config.MORPHOMETRICS_DIR
        csv_folder = config.CSV_DIR
        out_csv = csv_folder / "Morphometrics.csv"
        df = pd.read_csv(out_csv)

        if df["city"].nunique() > len(city_list):
            logger.info("CSV exists and has more cities. Skipping.")
            return

        df_full = pd.DataFrame()
        for file in morpho_folder.iterdir():
            if " - morpho.gpkg" in file.name:
                city_name = file.stem.split(" - morpho")[0].strip()
                gdf = gpd.read_file(file)
                gdf["city"] = city_name
                df_full = pd.concat([df_full, gdf])

        # Save
        df_full.to_csv(out_csv, index=None)
        logger.info("CSV: Saved %s", out_csv)
