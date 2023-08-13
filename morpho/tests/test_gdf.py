import geopandas as gpd

from morpho.layers import get_buildings, get_polygons, get_streets

city = "Raleigh"
gdf, gdf_collapsed = get_polygons(city)
gdf = gdf.head()


def test_gdf_is_gdf():
    assert isinstance(gdf, gpd.GeoDataFrame)


def test_gdf_columns():
    """Test that the GeoDataFrame has the expected columns."""
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


def test_geodataframe_not_empty():
    assert len(gdf) > 0


def test_gdf_collapsed():
    assert len(gdf_collapsed) == 1


def test_gdf_collapsed_columns():
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
    actual_columns = list(gdf_collapsed.columns)
    assert all(column in actual_columns for column in expected_columns)


buildings_gdf = get_buildings(city, gdf_collapsed, save=False)


def test_buildings_is_gdf():
    assert isinstance(buildings_gdf, gpd.GeoDataFrame)


def test_buildings_columns():
    expected_columns = ["geometry", "name"]
    actual_columns = list(buildings_gdf.columns)
    assert all(column in actual_columns for column in expected_columns)


streets_gdf = get_streets(city, gdf_collapsed, save=False)


def test_streets_is_gdf():
    assert isinstance(streets_gdf, gpd.GeoDataFrame)


def test_streets():
    expected_columns = [
        "osmid",
        "name",
        "highway",
        "maxspeed",
        "oneway",
        "reversed",
        "length",
        "geometry",
        "lanes",
        "bridge",
        "ref",
        "access",
        "junction",
        "width",
        "tunnel",
    ]
    actual_columns = list(streets_gdf.columns)
    assert all(column in actual_columns for column in expected_columns)
