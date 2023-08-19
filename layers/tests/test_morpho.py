"""Tests for the get_morphometrics() function"""

import networkx as nx
import numpy as np
import pandas as pd
import pytest

from layers.layers import get_polygons
from layers.morpho.helpers import (
    clean_gdf,
    count_and_merge,
    get_area,
    get_bearings,
    get_fractal_dimension,
    get_graph,
    get_orientation_order,
)


@pytest.fixture(scope="module")
def gdf():
    """Return a GeoDataFrame of the city of Raleigh"""
    city = "Raleigh"
    gdf_, _ = get_polygons(city)
    gdf_ = gdf_.head()
    gdf_ = clean_gdf(gdf_)
    return gdf_


@pytest.fixture(scope="module")
def G(gdf):
    """Return a networkx Graph of the city of Raleigh"""
    polygon = gdf["geometry"][4]
    G = get_graph(polygon)
    return G


@pytest.fixture(scope="module")
def bearings(G):
    return get_bearings(G)


@pytest.fixture(scope="module")
def count_and_merge_fixture(bearings):
    return count_and_merge(36, bearings)


@pytest.fixture(scope="module")
def orientation_order(count_and_merge_fixture):
    return get_orientation_order(count_and_merge_fixture)


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
    """Test that get_fractal_dimension returns a float"""
    result = get_fractal_dimension(G)
    assert isinstance(result, float)


def test_bearings_is_series(bearings):
    """Test that get_bearings returns a pandas Series"""
    assert isinstance(bearings, pd.Series)


def test_bearings_not_null(bearings):
    """Test that get_bearings returns a pandas Series with no null values"""
    assert bearings.isna().sum() == 0


def test_count_and_merge_is_ndarray(count_and_merge_fixture):
    """Test that count_and_merge returns a numpy array"""
    assert isinstance(count_and_merge_fixture, np.ndarray)


def test_count_and_merge_not_null(count_and_merge_fixture):
    """Test that count_and_merge returns a numpy array"""
    assert len(count_and_merge_fixture) > 0


def test_orientation_order(orientation_order):
    """Test that get_orientation_order returns a float"""
    assert isinstance(orientation_order, float)
