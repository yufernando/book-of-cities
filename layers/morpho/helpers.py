"""
Helper functions
"""
import math
import os

import imageio.v2 as imageio
import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd
from shapely.errors import GEOSException

# import warnings


# warnings.filterwarnings("ignore")


def reverse_bearing(x):
    """Reverse bearing"""
    return x + 180 if x < 180 else x - 180


def get_bearings(G):
    """Get bearings"""
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
        bearings = pd.concat([b, b.map(reverse_bearing)]).reset_index(drop="True")
    else:
        # don't weight bearings, just take one value per street segment
        b = pd.Series([d["bearing"] for u, v, k, d in Gu.edges(keys=True, data=True)])
        bearings = pd.concat([b, b.map(reverse_bearing)]).reset_index(drop="True")

    return bearings


def count_and_merge(n: int, bearings: pd.Series) -> np.ndarray:
    """Count and merge"""
    # make twice as many bins as desired, then merge them in pairs
    # prevents bin-edge effects around common values like 0° and 90°
    n = n * 2
    bins = np.arange(n + 1) * 360 / n
    count, _ = np.histogram(bearings, bins=bins)

    # move the last bin to the front, so eg 0.01° and 359.99° will be binned together
    count = np.roll(count, 1)
    return count[::2] + count[1::2]


def get_orientation_order(count: np.ndarray) -> float:
    """Calculate orientation order"""
    try:
        H0 = 0
        # for i in range(len(count)):
        for c in count:
            Pi = c / sum(count)
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


def get_graph(polygon):
    """Get networkX graph from polygon."""
    # get primary geometry and load network
    graph = ox.graph_from_polygon(
        polygon,
        network_type="drive",
        simplify=True,
        retain_all=False,
        truncate_by_edge=True,
        # clean_periphery=True,
        custom_filter=None,
    )
    return graph


def clean_gdf(gdf):
    """Clean gdf."""
    gdf["Center_point"] = gdf["geometry"].to_crs("+proj=cea").centroid.to_crs(4326)
    # Extract lat and lon from the centerpoint
    try:
        gdf["lon"] = gdf["Center_point"].map(lambda p: p.x)
        gdf["lat"] = gdf["Center_point"].map(lambda p: p.y)
    except GEOSException:
        pass

    gdf = gdf.drop(["Center_point"], axis=1)

    # Ensure crs is correct
    gdf = ox.project_gdf(gdf, to_crs="epsg:4326", to_latlong=False)
    return gdf


def get_area(gdf):
    """Get area of every polygon in the gdf."""
    temp = gdf.copy()
    temp = temp.to_crs("epsg:32630")
    temp["area_m2"] = temp["geometry"].area
    gdf["area_m2"] = temp["area_m2"]
    return gdf


def get_fractal_dimension(graph):
    """Get fractal dimension of street network."""
    # fp = f"./street-network-{ID}.png"
    filepath = "./street-network.png"
    ox.plot_graph(
        graph,
        bgcolor="white",
        node_color="black",
        edge_color="black",
        show=False,
        close=True,
        dpi=150,
        save=True,
        filepath=filepath,
    )
    # I = imageio.imread(fp, as_gray="True")/255.0
    image = imageio.imread(filepath, mode="L") / 255.0
    # get_ipython().system(" rm $fp # comment if you want to save the plot")
    os.remove(filepath)
    # print("Deleted:", fp)
    return -fractal_dimension(image)


def get_entropy(graph: nx.Graph) -> float:
    """Get entropy of street orientation order."""
    bearings = get_bearings(graph)
    count = count_and_merge(36, bearings)
    return get_orientation_order(count)
