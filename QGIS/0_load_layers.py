"""
Load Layers and Apply Styles
Load Buildings, Streets and Morphometrics and applies styles.
"""

# Import packages
import sys
from pathlib import Path

# Add code directory to path to import config
# Assumes QGIS script is in code/QGIS/, so go up one level
code_dir = Path(__file__).resolve().parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

import config

# Choose full layers
full = False

# City
city = Path(QgsProject.instance().fileName()).stem
print("City:", city)

# Use config paths - QGIS_DATA_ROOT points to the research data folder
root_folder = config.QGIS_DATA_ROOT.parent  # Research folder root
data_folder = config.QGIS_DATA_ROOT  # data/ subfolder
boundary_folder = data_folder / "0_boundaries"
project = QgsProject.instance()
root = project.layerTreeRoot()


# Dissolved
input_file = str(boundary_folder / f"{city}/{city}.gpkg") + f"|layername={city}"
output_file = str(boundary_folder / f"{city}/{city} Dissolved.gpkg")

processing.run(
    "native:dissolve", {"INPUT": input_file, "FIELD": [], "OUTPUT": output_file}
)

layer = iface.addVectorLayer(output_file, "", "ogr")
layer.setName("Dissolved")
layer.loadNamedStyle(str(data_folder / "3_QGIS/styles/Dissolved.qml"))
layer.triggerRepaint()
print("Applied style to Dissolved")


# Load layers
layer_name_list = [
    "Entropy",
    "Fractal Dimension",
    "Average Street Length",
    "Betweenness",
    "Building Area",
    "Building Compactness",
]

if full:
    # Full layers
    layer_name_list = [
        "Entropy",
        "Fractal Dimension",
        "Average Street Length",
        "Betweenness",
        "Building Area",
        "Building Compactness",
        "Area m2",
        "Compactness Area",
        "Diameter Periphery",
        "Streets Per Node",
        "Streets Per Node Proportion",
        "Intersection Density",
        "Street Density",
        "Circuity",
        "Node Connectivity",
        "PageRank",
        "Closeness Local",
        "Closeness Global",
        "Straightness",
        "Tesselation Area",
        "Building Orientation",
        "Tesselation Orientation",
        "Building Alignment",
        "Street Alignment",
        "Street Width",
        "Street Width Deviations",
        "Street Heights",
        "Street Heights Deviations",
        "Street Profile",
        "Area",
        "Built Area",
        "Street Length",
        "Building Height",
        "Building Volume",
    ]


for layer_name in ["Buildings", "Streets"]:
    layer_path = data_folder / f"1_buildings_streets/{city} - {layer_name}.gpkg"
    layer = iface.addVectorLayer(str(layer_path), "", "ogr")
    layer.setName(layer_name)
    print(f"Loaded {layer_name}")


for layer_name in layer_name_list:
    layer_path = data_folder / f"2_morphometrics/{city} - morpho.gpkg"
    layer = iface.addVectorLayer(str(layer_path), "", "ogr")
    layer.setName(layer_name)
    print(f"{city}: loaded {layer_name}")


# Apply styles
def apply_styles(layer_name_list):
    layer_name_list = layer_name_list + ["Buildings", "Streets", city]
    print(layer_name_list)

    for layer_name in layer_name_list:
        layer = project.mapLayersByName(layer_name)[0]
        style_file = str(data_folder / f"3_QGIS/styles/{layer_name}.qml")
        if layer_name == city:
            style_file = str(data_folder / "3_QGIS/styles/Boundary.qml")
        layer.loadNamedStyle(style_file)
        layer.triggerRepaint()
        print("Applied style to", layer_name)


apply_styles(layer_name_list)

iface.messageBar().pushMessage(
    "Success", f"Loaded all layers for {city}", level=3, duration=5
)
