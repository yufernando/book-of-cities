#!/usr/bin/env python
# coding: utf-8
"""
Get Buildings and Streets and run Morphometrics
"""
import logging
import os
import sys
import time
import warnings
from pathlib import Path

import geopandas as gpd

# import imageio
import imageio.v2 as imageio
import momepy
import numpy as np
import osmnx as ox
from shapely.errors import GEOSException

from helpers import (
    Usage,
    count_and_merge,
    find_next_city,
    format_time,
    fractal_dimension,
    get_bearings,
    get_logger,
    get_orientation_order,
    help_message,
    pp_compactness,
)

warnings.filterwarnings("ignore")

logger = get_logger()


# Helper functions
data_folder = Path("../data/")


def get_polygons(city):
    input_file = data_folder / "0_boundaries" / city / (city + ".gpkg")

    gdf = gpd.read_file(input_file, driver="GPKG")
    logger.info(f"Boundaries: Input {input_file} ({len(gdf)} polygons)")
    if len(gdf) > 200:
        raise ValueError(f"File too large: {len(gdf)} polygons.")

    # Force gdf projection
    gdf = ox.project_gdf(gdf, to_crs="epsg:4326", to_latlong=False)

    # Create unique ID
    gdf = gdf.reset_index(drop=True)
    gdf["UID"] = gdf.index

    gdf["collapse"] = 0
    gdf_collapsed = gdf.dissolve(by="collapse")

    return gdf, gdf_collapsed


def get_buildings(city, gdf_collapsed, save=True):
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

    if save:
        # Save
        out_file = data_folder / "1_buildings_streets" / (city + " - Buildings.gpkg")
        if out_file.exists():
            out_file.unlink()
        buildings_save.to_file(out_file, driver="GPKG")
        logger.info(f"Buildings:  Saved {out_file}")


def get_streets(city, gdf_collapsed, save=True):
    # Get Streets
    logger.info("Streets:    Downloading all streets.")
    G = ox.graph_from_polygon(
        gdf_collapsed["geometry"][0], network_type="drive", retain_all=True
    )

    # Remove nodes to export to geopackage
    gdf_streets = ox.utils_graph.graph_to_gdfs(G, nodes=False)
    for column in gdf_streets.columns:
        gdf_streets[column] = gdf_streets[column].apply(
            lambda x: ", ".join(map(str, x)) if isinstance(x, list) else x
        )

    if save:
        # Save
        out_file = data_folder / "1_buildings_streets" / (city + " - Streets.gpkg")
        if out_file.exists():
            out_file.unlink()
        gdf_streets.to_file(out_file, driver="GPKG")
        # ox.save_graph_geopackage(G, filepath=out_file)
        logger.info(f"Streets:    Saved {out_file}")


def get_morphometrics(city, gdf, save=True):
    logger.info("Morphometrics...")

    # Clean data
    # gdf["Center_point"] = gdf["geometry"].centroid
    gdf["Center_point"] = gdf["geometry"].to_crs("+proj=cea").centroid.to_crs(4326)
    # Extract lat and lon from the centerpoint
    try:
        gdf["lon"] = gdf.Center_point.map(lambda p: p.x)
        gdf["lat"] = gdf.Center_point.map(lambda p: p.y)
    except GEOSException:
        pass

    gdf = gdf.drop(["Center_point"], axis=1)

    # Ensure crs is correct
    gdf = ox.project_gdf(gdf, to_crs="epsg:4326", to_latlong=False)

    # Calculate area of every shape
    temp = gdf.copy()
    # temp = temp.to_crs({"init": "epsg:32630"})
    temp = temp.to_crs("epsg:32630")
    temp["area_m^2"] = temp["geometry"].area
    gdf["area_m^2"] = temp["area_m^2"]

    # Define variables

    # Scale Complexity
    gdf["fractal-dimension"] = np.nan
    # Spatial Complexity and Connectivity
    gdf["shannon_entropy-street_orientation_order"] = np.nan
    gdf["avg_street_length"] = np.nan
    gdf["avg_betweenness_centrality"] = np.nan
    # Built Complexity/Morphology
    gdf["avg_building_area"] = np.nan
    gdf["avg_building_compactness"] = np.nan

    # Main loop
    last_ID = 0
    bookmark = True

    # iterate through boundaries
    for ID in gdf.index:
        # Pick up where we left off or the loop broke
        if (ID != last_ID) and bookmark:
            continue
        else:
            bookmark = False

        logger.info(f"Polygon {ID+1} out of {len(gdf)}: ID = {ID}")

        try:
            logger.debug("Getting graph, fractal dimension, entropy, street length")
            # get primary geometry and load network
            polygon = gdf.loc[ID, "geometry"]
            G = ox.graph_from_polygon(
                polygon,
                network_type="drive",
                simplify=True,
                retain_all=False,
                truncate_by_edge=True,
                # clean_periphery=True,
                custom_filter=None,
            )
        except Exception:
            pass

        ####################
        # Scale Complexity #
        ####################
        try:
            fp = f"./street-network-{ID}.png"
            ox.plot_graph(
                G,
                bgcolor="white",
                node_color="black",
                edge_color="black",
                show=False,
                close=True,
                dpi=150,
                save=True,
                filepath=fp,
            )
            # I = imageio.imread(fp, as_gray="True")/255.0
            IMAGE = imageio.imread(fp, mode="L") / 255.0
            # get_ipython().system(" rm $fp # comment if you want to save the plot")
            os.remove(fp)
            # print("Deleted:", fp)
            gdf.loc[ID, "fractal-dimension"] = -fractal_dimension(
                IMAGE
            )  # invert sign of fractal dimension
        except Exception:
            pass

        #######################################
        # Spatial Complexity and Connectivity #
        #######################################
        try:
            # get 'shannon_entropy-street_orientation_order'
            bearings = get_bearings(G, ID)
            count = count_and_merge(36, bearings)
            street_orientation_order = get_orientation_order(count)
            gdf.loc[
                ID, "shannon_entropy-street_orientation_order"
            ] = street_orientation_order
            # print(street_orientation_order)
        except Exception:
            pass

        try:
            # get basic stats from network
            basic = ox.stats.basic_stats(G, area=gdf.loc[ID, "area_m^2"])

            # allocate stats
            gdf.loc[ID, "avg_street_length"] = basic["street_length_avg"]
        except Exception:
            pass

        try:
            # multiple centrality assessment
            streets_graph = ox.projection.project_graph(G)
            edges = ox.graph_to_gdfs(
                ox.get_undirected(streets_graph),
                nodes=False,
                edges=True,
                node_geometry=False,
                fill_edge_geometry=True,
            )
            primal = momepy.gdf_to_nx(edges, approach="primal")
            logger.debug("Betweenness.")
            primal = momepy.betweenness_centrality(
                primal, name="betweenness_metric_n", mode="nodes", weight="mm_len"
            )
            nodes = momepy.nx_to_gdf(primal, lines=False)

            gdf.loc[ID, "avg_betweenness_centrality"] = np.mean(
                nodes["betweenness_metric_n"]
            )
        except Exception:
            pass

        ###############################
        # Built Complexity/Morphology #
        ###############################
        try:
            logger.debug("Building area, compactness.")
            buildings_gdf = ox.features_from_polygon(polygon, tags={"building": True})
            buildings_gdf_projected = ox.project_gdf(buildings_gdf)
            buildings_gdf_projected = buildings_gdf_projected.reset_index()
            buildings_gdf_projected = buildings_gdf_projected[
                buildings_gdf_projected.geom_type.isin(["Polygon", "MultiPolygon"])
            ]

            verbose = True if logger.getEffectiveLevel() <= logging.DEBUG else False

            buildings = momepy.preprocess(
                buildings_gdf_projected,
                size=30,
                compactness=True,
                islands=True,
                verbose=verbose,
            )
            buildings["uID"] = momepy.unique_id(buildings)
        except Exception as e:
            import traceback

            traceback
            print(e)
            breakpoint()
            pass

        try:
            blg_area = momepy.Area(buildings)
            buildings["area"] = blg_area.series
            gdf.loc[ID, "avg_building_area"] = buildings["area"].mean()
        except Exception:
            pass

        try:
            buildings["compactness"] = buildings["geometry"].apply(
                lambda x: pp_compactness(x)
            )
            gdf.loc[ID, "avg_building_compactness"] = buildings["compactness"].mean()
        except Exception:
            pass

    gdf["UID"] = gdf.index

    # Report data availability
    vars_of_interest = [
        "avg_betweenness_centrality",
        "fractal-dimension",
        "shannon_entropy-street_orientation_order",
        "avg_street_length",
        "avg_building_area",
        "avg_building_compactness",
    ]
    for variable in vars_of_interest:
        if gdf[variable].isna().all():
            logger.info(f"{variable:<40} -> missing")
        else:
            logger.info(f"{variable:<40} -> available")

    # Save file
    if save:
        out_file = data_folder / "2_morphometrics" / (city + " - morpho.gpkg")
        gdf.to_file(out_file, driver="GPKG")
        logger.info(f"Morphometrics: Saved {out_file}")


def main_loop(city_list):
    logger.info(f"City list:  {', '.join(city_list)}")
    for city in city_list:
        logger.info(f"City:       {city}")
        t0 = time.perf_counter()

        gdf, gdf_collapsed = get_polygons(city)
        get_streets(city, gdf_collapsed)
        get_buildings(city, gdf_collapsed)
        get_morphometrics(city, gdf)

        t1 = time.perf_counter()
        logger.info(f"Done: {city}. Time elapsed: {format_time(t1 - t0)}")


def main():
    if len(sys.argv) == 1:
        raise Usage(
            "Must provide arguments.\n" + help_message.format(Path(__file__).name)
        )

    city_file_provided = False

    if Path(sys.argv[1]).is_file():  # first argument is "cities.txt"
        city_file_provided = True
        with open(sys.argv[1]) as f:
            cities_list = [
                city.strip().split(":")[0].split(",")[0] for city in f.readlines()
            ]
        sys.argv = sys.argv[1:]  # remove "cities.txt" from sys.argv

    if sys.argv[1] == "start":
        if not city_file_provided:
            raise Usage(
                "Must provide a list of cities in a text file.\n"
                + help_message.format(Path(__file__).name)
            )
        if len(sys.argv) > 3:
            raise Usage(
                "Too many arguments.\n" + help_message.format(Path(__file__).name)
            )
        start_loc = cities_list.index(sys.argv[2])
        city_list = cities_list[start_loc:]
    else:
        city_list = sys.argv[1:]

    main_loop(city_list)

    if city_file_provided:
        next_city = find_next_city(cities_list, city_list[0])
        logger.info(f"Next: {next_city}")


if __name__ == "__main__":
    main()
