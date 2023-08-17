import geopandas as gpd
import pytest

from morpho.layers import get_buildings, get_polygons, get_streets

city = "test"


@pytest.fixture(scope="module")
def polygons():
    gdf, gdf_collapsed = get_polygons(city)
    return gdf, gdf_collapsed


@pytest.fixture(scope="module")
def buildings_gdf(polygons):
    _, gdf_collapsed = polygons
    buildings_gdf = get_buildings(city, gdf_collapsed, save=False)
    return buildings_gdf


@pytest.fixture(scope="module")
def streets_gdf(polygons):
    _, gdf_collapsed = polygons
    streets_gdf = get_streets(city, gdf_collapsed, save=False)
    return streets_gdf


def test_gdf_is_gdf(polygons):
    gdf, _ = polygons
    assert isinstance(gdf, gpd.GeoDataFrame)


def test_gdf_columns(polygons):
    """Test that the GeoDataFrame has the expected columns."""
    gdf, _ = polygons
    expected_columns = [
        "STATEFP",
        "COUNTYFP",
        "TRACTCE",
        "GEOID",
        "NAME",
        "NAMELSAD",
        "MTFCC",
        "FUNCSTAT",
        "ALAND",
        "AWATER",
        "INTPTLAT",
        "INTPTLON",
        "geometry",
        "UID",
        "collapse",
    ]
    actual_columns = list(gdf.columns)
    assert all(column in actual_columns for column in expected_columns)


def test_geodataframe_not_empty(polygons):
    gdf, _ = polygons
    assert len(gdf) > 0


def test_gdf_collapsed(polygons):
    """Test that the Collapsed GeoDataFrame has one row."""
    _, gdf_collapsed = polygons
    assert len(gdf_collapsed) == 1


def test_gdf_collapsed_columns(polygons):
    """Test that the Collapsed GeoDataFrame has the expected columns."""
    expected_columns = [
        "geometry",
        "STATEFP",
        "COUNTYFP",
        "TRACTCE",
        "GEOID",
        "NAME",
        "NAMELSAD",
        "MTFCC",
        "FUNCSTAT",
        "ALAND",
        "AWATER",
        "INTPTLAT",
        "INTPTLON",
        "UID",
    ]
    _, gdf_collapsed = polygons
    actual_columns = list(gdf_collapsed.columns)
    assert all(column in actual_columns for column in expected_columns)


def test_buildings_is_gdf(buildings_gdf):
    assert isinstance(buildings_gdf, gpd.GeoDataFrame)


def test_buildings_columns(buildings_gdf):
    expected_columns = ["geometry", "name"]
    actual_columns = list(buildings_gdf.columns)
    assert all(column in actual_columns for column in expected_columns)


def test_streets_is_gdf(streets_gdf):
    assert isinstance(streets_gdf, gpd.GeoDataFrame)


def test_streets(streets_gdf):
    """Test that the streets GeoDataFrame has the expected columns."""
    expected_columns = [
        "osmid",
        "oneway",
        "lanes",
        "name",
        "highway",
        "reversed",
        "length",
        "geometry",
        "access",
        "maxspeed",
        "width",
        "junction",
    ]
    actual_columns = list(streets_gdf.columns)
    assert all(column in actual_columns for column in expected_columns)
