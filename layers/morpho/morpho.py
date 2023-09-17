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


def get_variables_list(full: bool) -> list:
    """Get list of variables to be calculated."""
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

    # Extra variables
    extra_vars = ["avg_node_degree"]

    # Initialize variables as np.nan
    all_vars = scale_vars + spatial_vars + built_vars + infra_vars + extra_vars
    return all_vars


def add_scale_vars(gdf, index, graph, polygon, full):
    """Add scale variables to gdf."""
    logger.debug("Scale Complexity.")

    gdf.loc[index, "fractal-dimension"] = get_fractal_dimension(graph)

    if full:
        gdf.loc[index, "compactness-area"] = pp_compactness(polygon)
        gdf.loc[index, "diameter-periphery"] = nx.diameter(graph.to_undirected())

        return gdf


def add_node_degree(gdf, index, street_graph):
    try:
        result = momepy.mean_node_degree(street_graph, verbose=False)
        gdf.loc[index, "avg_node_degree"] = result
    except TypeError:
        import traceback

        traceback.print_exc()
        breakpoint()

    return gdf


def add_spatial_vars(gdf, index, graph, edges, full, verbose=False):
    """Add spatial variables to gdf."""
    try:
        gdf.loc[index, "shannon_entropy-street_orientation_order"] = get_entropy(graph)
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
        gdf.loc[index, "avg_node_connectivity"] = np.mean(nx.node_connectivity(graph))
        gdf.loc[index, "avg_PageRank"] = np.mean(list(nx.pagerank(graph).values()))

    # Multiple centrality assessment
    logger.debug("Multiple centrality assessment")

    logger.debug("gdf to nx.")
    primal = momepy.gdf_to_nx(edges, approach="primal")

    # Debug
    try:
        avg_node_degree = momepy.mean_node_degree(primal, verbose=False)
        logger.info("avg_node_degree=%s", avg_node_degree)
        gdf.loc[index, "avg_node_degree"] = avg_node_degree
    except TypeError as e:
        logger.debug("Error calculating node degree: %s", e)

    logger.debug("Betweenness.")
    primal = momepy.betweenness_centrality(
        primal, name="betweenness_metric_n", mode="nodes", weight="mm_len"
    )
    nodes = momepy.nx_to_gdf(primal, lines=False)
    gdf.loc[index, "avg_betweenness_centrality"] = np.mean(
        nodes["betweenness_metric_n"]
    )

    if full:
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
        logger.debug("Straightness centrality.")
        primal = momepy.straightness_centrality(primal)
        logger.debug("nx to gdf.")
        nodes = momepy.nx_to_gdf(primal, lines=False)

        gdf.loc[index, "avg_local_closeness_centrality"] = np.mean(
            nodes["closeness_local"]
        )
        gdf.loc[index, "avg_global_closeness_centrality"] = np.mean(
            nodes["closeness_global"]
        )
        gdf.loc[index, "avg_straightness_centrality"] = np.mean(nodes["straightness"])
    return gdf, basic


def add_built_vars(gdf, index, edges, polygon, verbose=False):
    """Add built variables to gdf."""
    logger.debug("Building area, compactness.")
    try:
        buildings_gdf = ox.features_from_polygon(polygon, tags={"building": True})
    except ox._errors.InsufficientResponseError:
        logger.debug("No data elements in server response.")
        return gdf, None

    if buildings_gdf.empty:
        logger.debug("No buildings in polygon.")
        return gdf, None

    buildings_gdf_projected = ox.project_gdf(buildings_gdf)
    buildings_gdf_projected = buildings_gdf_projected.reset_index()
    buildings_gdf_projected = buildings_gdf_projected[
        buildings_gdf_projected.geom_type.isin(["Polygon", "MultiPolygon"])
    ]
    if buildings_gdf_projected.empty:
        logger.debug("Projected buildings_gdf is empty.")
        return gdf, None

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
    gdf.loc[index, "avg_tessellation_orientation"] = tessellation["orientation"].mean()

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
        gdf.loc[index, "avg_width_deviations-street_profile"] = edges["widths"].mean()
        gdf.loc[index, "avg_openness-street_profile"] = edges["widths"].mean()
        gdf.loc[index, "avg_heights-street_profile"] = edges["widths"].mean()
        gdf.loc[index, "avg_heights_deviations-street_profile"] = edges["widths"].mean()
        gdf.loc[index, "avg_profile-street_profile"] = edges["widths"].mean()
    except KeyError:  # OSM did not provide height
        pass
    except ValueError:
        if "height" in buildings.columns:
            # check if we are incorrectly ignoring the error
            logger.error(
                "Skipped momepy.StreetProfile but buildings dataframe had height column."
            )

    buildings["compactness"] = buildings["geometry"].apply(pp_compactness)
    gdf.loc[index, "avg_building_compactness"] = buildings["compactness"].mean()
    return gdf, buildings


def add_infra_vars(gdf, index, buildings, basic):
    """Add infrastructure variables to gdf."""
    gdf.loc[index, "total_area"] = gdf.loc[index, "area_m2"]
    if buildings is not None:
        gdf.loc[index, "total_built_area"] = buildings["area"].sum()
    gdf.loc[index, "total_street_length"] = basic["street_length_total"]
    return gdf


def get_morphometrics(
    gdf: gpd.GeoDataFrame, full: bool = True, verbose: bool = False
) -> None:
    """Get morphometrics for a city."""
    logger.info("Morphometrics:")

    # Setup
    gdf = clean_gdf(gdf)
    gdf = get_area(gdf)
    all_vars = get_variables_list(full)
    for variable in all_vars:
        gdf[variable] = np.nan

    for index in gdf.index:
        logger.info("Polygon %s out of %s: id = %s", index + 1, len(gdf), index)

        # Setup
        polygon = gdf.loc[index, "geometry"]
        try:
            graph = get_graph(polygon)
        except ValueError as e:
            logger.error(e)
            continue
        streets_graph = ox.projection.project_graph(graph)
        edges = ox.graph_to_gdfs(
            ox.get_undirected(streets_graph),
            nodes=False,
            edges=True,
            node_geometry=False,
            fill_edge_geometry=True,
        )

        # Debug
        # gdf = add_node_degree(gdf, index, streets_graph)

        # Scale Complexity
        gdf = add_scale_vars(gdf, index, graph, polygon, full)
        # Spatial Complexity and Connectivity
        gdf, basic = add_spatial_vars(gdf, index, graph, edges, full, verbose)
        # Built Complexity/Morphology
        gdf, buildings = add_built_vars(gdf, index, edges, polygon)
        # Infrastructure
        gdf = add_infra_vars(gdf, index, buildings, basic)

    # Report results
    for variable in all_vars:
        if gdf[variable].isna().all():
            logger.info("%-40s -> missing", variable)
        else:
            logger.info("%-40s -> available", variable)

    return gdf
