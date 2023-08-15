import networkx as nx

from morpho.layers import (
    clean_gdf,
    get_area,
    get_entropy,
    get_fractal_dimension,
    get_graph,
    get_polygons,
)

city = "Raleigh"
gdf, gdf_collapsed = get_polygons(city)
gdf = gdf.head()
gdf = clean_gdf(gdf)


def test_missing_lat():
    """Test that missing latitude is below 10%"""
    missing_lon = gdf["lat"].isna().sum()
    assert missing_lon / len(gdf) < 0.1


def test_missing_lon():
    """Test that missing longitude is below 10%"""
    missing_lon = gdf["lon"].isna().sum()
    assert missing_lon / len(gdf) < 0.1


polygon = gdf["geometry"][0]
G = get_graph(polygon)


def test_get_graph():
    """Test that get_graph returns a networkx Graph"""
    assert isinstance(G, nx.Graph)


def test_get_graph_not_empty():
    """Test that get_graph returns a networkx Graph with more than one node"""
    assert len(G) > 1


def test_area():
    """Test that missing area is less than 10%"""
    gdf_new = get_area(gdf)
    assert gdf_new["area_m2"].isna().sum() / len(gdf_new) < 0.1


def test_fractal_dimension():
    result = get_fractal_dimension(G)
    print(result)
    assert isinstance(result, float)


def test_entropy():
    result = get_entropy(G, ID)  # Revise this, you cannot have ID here
    assert isinstance(result, float)
