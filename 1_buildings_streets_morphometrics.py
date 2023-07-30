#!/usr/bin/env python
# coding: utf-8
"""
Get Buildings and Streets and run Morphometrics
"""
# Import modules

import logging
import os
import time
import warnings
from pathlib import Path

import geopandas as gpd
import imageio
import momepy
import numpy as np
import osmnx as ox

from helpers import (
    count_and_merge,
    fractal_dimension,
    get_bearings,
    get_orientation_order,
    pp_compactness,
)

warnings.filterwarnings("ignore")

logging.basicConfig(
    filename="morphometrics.log",
    filemode="w",
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    level=logging.INFO,
)

# # Choose City

city_list = [
    "Melbourne",
    "Jerusalem",
    "Buenos Aires",
    "Paris",
    "Rotterdam",
    "Nashville",
    "Singapore",
    "Cape Town",
    "New York",
    "Los Angeles",
    "Chicago",
    "Boston",
    "Austin",
    "Seattle",
    "Philadelphia",
    "Pittsburgh",
    "Washington DC",
    "San Francisco",
    "SF Bay Area ",
    "Raleigh",
    "Milwaukee",
    "Portland",
    "San Diego",
    "Denver",
    "Miami",
    "Saint Louis",
    "Houston",
    "Atlanta",
    "Phoenix",
    "Detroit",
    "Minneapolis",
    "Savannah",
    "Charlotte",
    "Las Vegas",
    "Cincinnati",
    "Kansas City",
    "Nashville",
]

# city_list = city_list[8:12]
city_list = [city_list[8]]
logging.info(f"City list: {', '.join(city_list)}")

for city in city_list:
    logging.info(f"City: {city}")
    # Buildings and Streets

    # Read Geopackage
    data_folder = Path("../data/")
    input_file = data_folder / "0_boundaries" / city / (city + ".gpkg")

    logging.info(f"Input: {input_file}")
    gdf = gpd.read_file(input_file, driver="GPKG")
    # Force gdf projection
    gdf = ox.project_gdf(gdf, to_crs="epsg:4326", to_latlong=False)

    # Get Master polygon
    # Create unique ID
    gdf = gdf.reset_index(drop=True)
    gdf["UID"] = gdf.index
    # Establish bounds DataFrame (everything so we can do one query)
    gdf["collapse"] = 0
    gdf_collapsed = gdf.dissolve(by="collapse")

    # Get Streets
    G = ox.graph_from_polygon(
        gdf_collapsed["geometry"][0], network_type="drive", retain_all=True
    )
    out_file = data_folder / "1_buildings_streets" / (city + " - streets.gpkg")
    ox.save_graph_geopackage(G, filepath=out_file)
    logging.info(f"Saved: {out_file}")

    # Get Buildings
    tags = {"building": True}
    buildings = ox.geometries_from_polygon(gdf_collapsed["geometry"][0], tags)
    buildings = buildings[["geometry", "name"]]
    buildings_save = buildings.drop(labels="node", axis=0)

    # Save
    out_file = data_folder / "1_buildings_streets" / (city + " - buildings.gpkg")
    buildings_save.to_file(out_file, driver="GPKG")
    logging.info(f"Saved: {out_file}")

    # Morphometrics
    # data_folder = Path("../data")
    # input_file = data_folder / "0_boundaries" / (city + ".gpkg")
    # logging.info(f"Reading: {input_file}")
    # gdf = gpd.read_file(input_file, driver="GPKG")
    logging.info("Running Morphometrics...")

    # Clean data
    gdf["Center_point"] = gdf["geometry"].centroid
    # Extract lat and lon from the centerpoint
    gdf["lon"] = gdf.Center_point.map(lambda p: p.x)
    gdf["lat"] = gdf.Center_point.map(lambda p: p.y)
    gdf = gdf.drop(["Center_point"], axis=1)

    # Ensure crs is correct
    gdf = ox.project_gdf(gdf, to_crs="epsg:4326", to_latlong=False)

    # Calculate area of every shape
    temp = gdf.copy()
    temp = temp.to_crs({"init": "epsg:32630"})
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

    t0 = time.perf_counter()
    # iterate through boundaries
    for ID in gdf.index:
        # Pick up where we left off or the loop broke
        if (ID != last_ID) and bookmark:
            continue
        else:
            bookmark = False

        logging.info(f"Run {ID+1} out of {len(gdf)}: ID = {ID}")

        try:
            # get primary geometry and load network
            polygon = gdf.loc[ID, "geometry"]
            G = ox.graph_from_polygon(
                polygon,
                network_type="drive",
                simplify=True,
                retain_all=False,
                truncate_by_edge=True,
                clean_periphery=True,
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
            buildings_gdf = ox.geometries_from_polygon(polygon, tags={"building": True})
            buildings_gdf_projected = ox.project_gdf(buildings_gdf)
            buildings_gdf_projected = buildings_gdf_projected.reset_index()
            buildings_gdf_projected = buildings_gdf_projected[
                buildings_gdf_projected.geom_type.isin(["Polygon", "MultiPolygon"])
            ]

            buildings = momepy.preprocess(
                buildings_gdf_projected, size=30, compactness=True, islands=True
            )
            buildings["uID"] = momepy.unique_id(buildings)
        except Exception:
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

    t1 = time.perf_counter()
    logging.info(f"Done. Time elapsed: {t1-t0:.0f} seconds.")

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
            logging.info(f"{variable:<40} -> missing")
        else:
            logging.info(f"{variable:<40} -> available")

    # Save file
    out_file = data_folder / "2_morphometrics" / (city + " - morpho.gpkg")
    gdf.to_file(out_file, driver="GPKG")
    logging.info(f"Saved: {out_file}")
