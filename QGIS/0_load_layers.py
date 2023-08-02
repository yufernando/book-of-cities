"""
Load Layers and Apply Styles

Load Buildings, Streets and Morphometrics and applies styles.

Instructions: choose city.
"""
# Choose city
city = "Cincinnati"

# Import packages
from pathlib import Path
root_folder = Path("/Users/fer/aretian-drive/Research/Book of Cities/")
data_folder = root_folder / "data/"
boundary_folder = data_folder / "0_boundaries"
project = QgsProject.instance()
root = project.layerTreeRoot()


# Dissolved
input_file = str(boundary_folder / f"{city}/{city}.gpkg") + f"|layername={city}"
output_file = str(boundary_folder / f"{city}/{city} Dissolved.gpkg")

processing.run("native:dissolve", {
    'INPUT':input_file,
    'FIELD':[],
    'OUTPUT':output_file})

layer = iface.addVectorLayer(output_file, "", "ogr")
layer.setName("Dissolved")
layer.loadNamedStyle(str(root_folder / f"data/3_QGIS/styles/Dissolved.qml"))
layer.triggerRepaint()
print("Applied style to Dissolved")


# Load layers
layer_name_list = [
    "Entropy", 
    "Fractal Dimension", 
    "Average Street Length",
    "Betweenness",
    "Building Area",
    "Building Compactness"]


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

def apply_styles():
    layer_name_list = [
        "Entropy", 
        "Fractal Dimension", 
        "Average Street Length",
        "Betweenness",
        "Building Area",
        "Building Compactness",
        "Buildings",
        "Streets",
        city]

    for layer_name in layer_name_list:
        layer = project.mapLayersByName(layer_name)[0]
        style_file = str(root_folder / f"data/3_QGIS/styles/{layer_name}.qml")
        if layer_name == city:
            style_file = str(root_folder / f"data/3_QGIS/styles/Boundary.qml")
        layer.loadNamedStyle(style_file)
        layer.triggerRepaint()
        print("Applied style to", layer_name)
        

apply_styles()

iface.messageBar().pushMessage("Success", f"Loaded all layers for {city}", level=3, duration=5)






