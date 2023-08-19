#!/usr/bin/env python
# coding: utf-8
"""
Get Buildings and Streets and run Morphometrics
"""
import logging
import sys
import time
from pathlib import Path

import geopandas as gpd
import osmnx as ox

from layers.helpers import find_next_city, format_time, parse_user_input
from layers.morpho import get_morphometrics

data_folder = Path("../data/")

logger = logging.getLogger("log")


def get_polygons(city):
    """Get polygons from city."""
    input_file = data_folder / "0_boundaries" / city / (city + ".gpkg")

    gdf = gpd.read_file(input_file, driver="GPKG")
    logger.info("Boundaries: Input %s (%s polygons)", input_file, len(gdf))
    if len(gdf) > 200:
        raise ValueError(f"{city} boundaries file too large: {len(gdf)} polygons.")

    # Force gdf projection
    gdf = ox.project_gdf(gdf, to_crs="epsg:4326", to_latlong=False)

    # Create unique ID
    gdf = gdf.reset_index(drop=True)
    gdf["UID"] = gdf.index

    gdf["collapse"] = 0
    gdf_collapsed = gdf.dissolve(by="collapse")

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


def get_city_layers(city, buildings=True, streets=True, morphometrics=True, save=True):
    """Get city layers."""
    logger.info("-----------------------------------------------------------------")
    logger.info("City:       %s", city)
    start = time.perf_counter()

    gdf, gdf_collapsed = get_polygons(city)

    if streets:
        gdf_streets = get_streets(gdf_collapsed)
        if save:
            out_file = data_folder / "1_buildings_streets" / (city + " - Streets.gpkg")
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
            out_file = (
                data_folder / "1_buildings_streets" / (city + " - Buildings.gpkg")
            )
            if out_file.exists():
                out_file.unlink()
            gdf_buildings.to_file(out_file, driver="GPKG")
            logger.info("Buildings:  Saved %s", out_file)
    else:
        logger.info("Buildings:  Skipped.")

    if morphometrics:
        gdf = get_morphometrics(gdf, full=True)
        if save:
            out_file = data_folder / "2_morphometrics" / (city + " - morpho.gpkg")
            gdf.to_file(out_file, driver="GPKG")
            logger.info("Morphometrics: Saved %s", out_file)
    else:
        logger.info("Morphometrics: Skipped.")

    end = time.perf_counter()
    logger.info("Done: %s. Time elapsed: %s", city, format_time(end - start))


def main(buildings=True, streets=True, morphometrics=True, csv_out=True):
    """Entrypoint."""
    city_list, cities_list, city_file_provided = parse_user_input(sys.argv)
    logger.info("City list:  %s", ", ".join(city_list))

    for city in city_list:
        try:
            get_city_layers(city, buildings, streets, morphometrics, save=True)
        except ValueError as e:
            logger.error(f"Boundaries: {e}")
            continue
        except Exception as e:
            logger.error(f"Error processing city {city}. Skipping.")
            logger.exception(e)  # logger.exception adds traceback and nice error format
            continue

    if city_file_provided:
        next_city = find_next_city(cities_list, city_list[0])
        logger.info("Next: %s", next_city)

    if csv_out:
        pass


if __name__ == "__main__":
    main()
