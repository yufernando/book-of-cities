"""
Morphometrics
"""
import logging
import warnings

import geopandas as gpd
import momepy
import networkx as nx
import numpy as np
import osmnx as ox

from layers.morpho.helpers import (
    clean_gdf,
    clean_heights,
    get_area,
    get_entropy,
    get_fractal_dimension,
    get_graph,
    pp_compactness,
)

warnings.filterwarnings("ignore")

logger = logging.getLogger("log")


def get_morphometrics(
    gdf: gpd.GeoDataFrame, full: bool = False, verbose: bool = False
) -> None:
    """Get morphometrics for a city."""
    gdf = clean_gdf(gdf)

    logger.info("Morphometrics...")
    gdf = get_area(gdf)

    # Define variables

    # Scale Complexity
    scale_vars = ["fractal-dimension"]
    if full:
        scale_extra_vars = ["compactness-area", "diameter-periphery"]
        scale_vars.extend(scale_extra_vars)

    # Spatial Complexity and Connectivity
    spatial_vars = [
        "shannon_entropy-street_orientation_order",
        "avg_street_length",
        "avg_betweenness_centrality",
    ]
    if full:
        spatial_extra_vars = [
            "avg_streets_per_node",
            "avg_proportion_streets_per_node",
            "intersection_density",
            "street_density",
            "avg_circuity",
            "avg_node_connectivity",
            "avg_PageRank",
            "avg_local_closeness_centrality",
            "avg_global_closeness_centrality",
            "avg_straightness_centrality",
        ]
        spatial_vars.extend(spatial_extra_vars)

    # Built Complexity/Morphology
    built_vars = ["avg_building_area", "avg_building_compactness"]
    if full:
        built_extra_vars = [
            "avg_tesselation_area",
            # "avg_building_height",
            # "avg_building_volume",
            "avg_building_orientation",
            "avg_tessellation_orientation",
            "avg_building_cell_alignment",
            "avg_street_alignment",
            "avg_width-street_profile",
            "avg_width_deviations-street_profile",
            "avg_openness-street_profile",
            "avg_heights-street_profile",
            "avg_heights_deviations-street_profile",
            "avg_profile-street_profile",
        ]
        built_vars.extend(built_extra_vars)

    # Infrastructure
    infra_vars = ["total_area", "total_built_area", "total_street_length"]

    # Initialize variables as np.nan
    all_vars = scale_vars + spatial_vars + built_vars + infra_vars
    for variable in all_vars:
        gdf[variable] = np.nan

    # Main loop
    for index in gdf.index:
        logger.info("Polygon %s out of %s: id = %s", index + 1, len(gdf), index)

        polygon = gdf.loc[index, "geometry"]

        try:
            graph = get_graph(polygon)
        except ValueError as e:
            logger.error(e)
            continue

        # Scale Complexity
        # -------------------
        logger.debug("Scale Complexity.")

        gdf.loc[index, "fractal-dimension"] = get_fractal_dimension(graph)

        if full:
            gdf.loc[index, "compactness-area"] = pp_compactness(polygon)
            gdf.loc[index, "diameter-periphery"] = nx.diameter(graph.to_undirected())

        # Spatial Complexity and Connectivity
        # --------------------------------------
        try:
            gdf.loc[index, "shannon_entropy-street_orientation_order"] = get_entropy(
                graph
            )
        except KeyError:  # this error is raised in get_bearings()
            pass

        # Basic Stats
        basic = ox.stats.basic_stats(graph, area=gdf.loc[index, "area_m2"])
        gdf.loc[index, "avg_street_length"] = basic["street_length_avg"]
        if full:
            gdf.loc[index, "avg_streets_per_node"] = basic["streets_per_node_avg"]
            gdf.loc[index, "avg_proportion_streets_per_node"] = np.mean(
                list(basic["streets_per_node_proportions"].values())
            )
            gdf.loc[index, "intersection_density"] = basic["node_density_km"]
            gdf.loc[index, "street_density"] = basic["street_density_km"]
            gdf.loc[index, "avg_circuity"] = basic["circuity_avg"]
            gdf.loc[index, "avg_node_connectivity"] = np.mean(
                nx.node_connectivity(graph)
            )
            gdf.loc[index, "avg_PageRank"] = np.mean(list(nx.pagerank(graph).values()))

        # multiple centrality assessment
        logger.debug("Multiple centrality assessment")
        streets_graph = ox.projection.project_graph(graph)
        logger.debug("Graph to gdfs.")
        edges = ox.graph_to_gdfs(
            ox.get_undirected(streets_graph),
            nodes=False,
            edges=True,
            node_geometry=False,
            fill_edge_geometry=True,
        )
        logger.debug("gdf to nx.")
        primal = momepy.gdf_to_nx(edges, approach="primal")
        logger.debug("Closeness centrality local.")
        primal = momepy.closeness_centrality(
            primal,
            radius=gdf.loc[index, "diameter-periphery"] * (1 / 4),
            name="closeness_local",
            distance="mm_len",
            weight="mm_len",
            verbose=verbose,
        )
        logger.debug("Closeness centrality global.")
        primal = momepy.closeness_centrality(
            primal, name="closeness_global", weight="mm_len"
        )
        logger.debug("Betweenness.")
        primal = momepy.betweenness_centrality(
            primal, name="betweenness_metric_n", mode="nodes", weight="mm_len"
        )
        logger.debug("Straightness centrality.")
        primal = momepy.straightness_centrality(primal)
        logger.debug("nx to gdf.")
        nodes = momepy.nx_to_gdf(primal, lines=False)

        gdf.loc[index, "avg_betweenness_centrality"] = np.mean(
            nodes["betweenness_metric_n"]
        )
        if full:
            gdf.loc[index, "avg_local_closeness_centrality"] = np.mean(
                nodes["closeness_local"]
            )
            gdf.loc[index, "avg_global_closeness_centrality"] = np.mean(
                nodes["closeness_global"]
            )
            gdf.loc[index, "avg_straightness_centrality"] = np.mean(
                nodes["straightness"]
            )

        # Built Complexity/Morphology
        # ------------------------------
        logger.debug("Building area, compactness.")
        buildings_gdf = ox.features_from_polygon(polygon, tags={"building": True})
        buildings_gdf_projected = ox.project_gdf(buildings_gdf)
        buildings_gdf_projected = buildings_gdf_projected.reset_index()
        buildings_gdf_projected = buildings_gdf_projected[
            buildings_gdf_projected.geom_type.isin(["Polygon", "MultiPolygon"])
        ]

        logger.debug("momepy preprocess.")
        buildings = momepy.preprocess(
            buildings_gdf_projected,
            size=30,
            compactness=True,
            islands=True,
            verbose=verbose,
        )
        buildings["uID"] = momepy.unique_id(buildings)

        logger.debug("momepy buffered limit.")
        limit = momepy.buffered_limit(buildings)

        logger.debug("momepy tessellation.")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tess = momepy.Tessellation(
                buildings, unique_id="uID", limit=limit, verbose=verbose
            )

        tessellation = tess.tessellation

        logger.debug("avg_building_area.")
        blg_area = momepy.Area(buildings)
        buildings["area"] = blg_area.series
        gdf.loc[index, "avg_building_area"] = buildings["area"].mean()

        logger.debug("avg_tesselation_area.")
        tes_area = momepy.Area(tessellation)
        tessellation["area"] = tes_area.series
        gdf.loc[index, "avg_tesselation_area"] = tessellation["area"].mean()

        logger.debug("building height.")
        try:
            buildings["height"] = buildings["height"].fillna(0).apply(clean_heights)
            if (buildings["height"] == 0).all():
                pass
            else:
                gdf.loc[index, "avg_building_height"] = buildings["height"].mean()
        except KeyError:  # OSM did not provide height
            pass

        logger.debug("avg_building_volume")
        try:
            if (buildings["height"] == 0).all():  # if height = 0 then volume = 0
                pass
            else:
                blg_volume = momepy.Volume(buildings, heights="height")
                buildings["volume"] = blg_volume.series
                gdf.loc[index, "avg_building_volume"] = buildings["volume"].mean()
        except KeyError:  # OSM did not provide height
            pass

        logger.debug("building orientation")
        buildings["orientation"] = momepy.Orientation(buildings, verbose=verbose).series
        gdf.loc[index, "avg_building_orientation"] = buildings["orientation"].mean()

        logger.debug("tessellation orientation")
        tessellation["orientation"] = momepy.Orientation(
            tessellation, verbose=verbose
        ).series
        gdf.loc[index, "avg_tessellation_orientation"] = tessellation[
            "orientation"
        ].mean()

        logger.debug("building cell alignment")
        blg_cell_align = momepy.CellAlignment(
            buildings, tessellation, "orientation", "orientation", "uID", "uID"
        )
        buildings["cell_align"] = blg_cell_align.series
        gdf.loc[index, "avg_building_cell_alignment"] = buildings["cell_align"].mean()

        logger.debug("Network ID")
        edges["networkID"] = momepy.unique_id(edges)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            buildings["networkID"] = momepy.get_network_id(
                buildings, edges, "networkID", verbose=verbose
            )
        buildings_net = buildings.loc[buildings.networkID >= 0]

        logger.debug("street alignment")
        str_align = momepy.StreetAlignment(
            buildings_net, edges, "orientation", "networkID", "networkID"
        )
        logger.debug("Assign street alignment to buildings dataframe.")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            buildings_net["str_align"] = str_align.series
        logger.debug("Average Street Alignment.")
        gdf.loc[index, "avg_street_alignment"] = buildings_net["str_align"].mean()

        logger.debug("Street profile")
        try:
            profile = momepy.StreetProfile(edges, buildings, heights="height")
            edges["widths"] = profile.w
            edges["width_deviations"] = profile.wd
            edges["openness"] = profile.o
            edges["heights"] = profile.h
            edges["heights_deviations"] = profile.hd
            edges["profile"] = profile.p

            gdf.loc[index, "avg_width-street_profile"] = edges["widths"].mean()
            gdf.loc[index, "avg_width_deviations-street_profile"] = edges[
                "widths"
            ].mean()
            gdf.loc[index, "avg_openness-street_profile"] = edges["widths"].mean()
            gdf.loc[index, "avg_heights-street_profile"] = edges["widths"].mean()
            gdf.loc[index, "avg_heights_deviations-street_profile"] = edges[
                "widths"
            ].mean()
            gdf.loc[index, "avg_profile-street_profile"] = edges["widths"].mean()
        except KeyError:  # OSM did not provide height
            pass

        buildings["compactness"] = buildings["geometry"].apply(pp_compactness)
        gdf.loc[index, "avg_building_compactness"] = buildings["compactness"].mean()

        # Infrastructure
        # ----------------
        gdf.loc[index, "total_area"] = gdf.loc[index, "area_m2"]
        gdf.loc[index, "total_built_area"] = buildings["area"].sum()
        gdf.loc[index, "total_street_length"] = basic["street_length_total"]

    # gdf["UID"] = gdf.index

    for variable in all_vars:
        if gdf[variable].isna().all():
            logger.info("%-40s -> missing", variable)
        else:
            logger.info("%-40s -> available", variable)

    return gdf
