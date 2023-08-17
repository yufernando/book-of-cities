import networkx as nx
import pandas as pd
import pytest

from morpho.helpers import get_bearings
from morpho.layers import (
    clean_gdf,
    get_area,
    get_entropy,
    get_fractal_dimension,
    get_graph,
    get_polygons,
)


@pytest.fixture
def gdf():
    city = "Raleigh"
    gdf, gdf_collapsed = get_polygons(city)
    gdf = gdf.head()
    gdf = clean_gdf(gdf)
    return gdf


@pytest.fixture
def G(gdf):
    polygon = gdf["geometry"][4]
    G = get_graph(polygon)
    return G


def test_missing_lat(gdf):
    """Test that missing latitude is below 10%"""
    missing_lon = gdf["lat"].isna().sum()
    assert missing_lon / len(gdf) < 0.1


def test_missing_lon(gdf):
    """Test that missing longitude is below 10%"""
    missing_lon = gdf["lon"].isna().sum()
    assert missing_lon / len(gdf) < 0.1


def test_area(gdf):
    """Test that missing area is less than 10%"""
    gdf = get_area(gdf)
    assert gdf["area_m2"].isna().sum() / len(gdf) < 0.1


def test_get_graph(G):
    """Test that get_graph returns a networkx Graph"""
    assert isinstance(G, nx.Graph)


def test_get_graph_not_empty(G):
    """Test that get_graph returns a networkx Graph with more than one node"""
    assert len(G) > 1


def test_fractal_dimension(G):
    result = get_fractal_dimension(G)
    assert isinstance(result, float)


def test_bearings_is_Series(G):
    result = get_bearings(G)
    assert isinstance(result, pd.Series)


def test_bearings_not_null(G):
    result = get_bearings(G)
    assert result.isna().sum() == 0
