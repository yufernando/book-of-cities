"""
Export images
Exports images from map layout to figs folder.
"""
# Choose city
city = "Mexico City"
# Choose full layers
full = False

# Import packages
from pathlib import Path

# Helper functions
project = QgsProject.instance()
root = project.layerTreeRoot()
root_folder = Path("/Users/fer/aretian-drive/Research/Book of Cities/")


def toggle_layer(layer_name, visible=True):
    layer = project.mapLayersByName(layer_name)[0]
    root.findLayer(layer.id()).setItemVisibilityChecked(visible)


def reset_all():
    allLayers = root.layerOrder()
    for layer in allLayers:
        root.findLayer(layer.id()).setItemVisibilityChecked(False)
    toggle_layer("Dark Matter (retina)")
    toggle_layer("Dissolved")


def save_image(output_file_path):
    output_file_path.parent.mkdir(exist_ok=True)
    layout = project.layoutManager().layoutByName("Map")
    export_settings = QgsLayoutExporter.ImageExportSettings()
    export_settings.dpi = 600
    exporter = QgsLayoutExporter(layout)
    exporter.exportToImage(str(output_file_path), export_settings)


def saved_message(file_name):
    iface.messageBar().pushMessage("Saved:", str(file_name), level=3, duration=5)


# Export Morphometrics
layer_name_list = [
    "Entropy",
    "Fractal Dimension",
    "Average Street Length",
    "Betweenness",
    "Building Area",
    "Building Compactness",
]

# Full layers
if full:
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

for layer_name in layer_name_list:
    reset_all()
    toggle_layer("Buildings")
    toggle_layer("Streets")
    toggle_layer(layer_name)
    output_file_path = root_folder / f"figs/{city}/{layer_name}.jpg"
    save_image(output_file_path)
    #    saved_message(output_file_path)
    print("Saved:", output_file_path)

# Export Buildings and Streets separately
layer_name_list = ["Buildings", "Streets"]
for layer_name in layer_name_list:
    reset_all()
    toggle_layer(layer_name)
    output_file_path = root_folder / f"figs/{city}/{layer_name}.jpg"
    save_image(output_file_path)
    #    saved_message(output_file_path)
    print("Saved:", output_file_path)

# Export Buildings and Streets jointly
reset_all()
toggle_layer("Buildings")
toggle_layer("Streets")
output_file_path = root_folder / f"figs/{city}/Buildings and Streets.jpg"
save_image(output_file_path)
# saved_message(output_file_path)
print("Saved:", output_file_path)

# Export Boundaries
reset_all()
toggle_layer(city)
output_file_path = root_folder / f"figs/{city}/Boundaries.jpg"
save_image(output_file_path)
# saved_message(output_file_path)
print("Saved:", output_file_path)

iface.messageBar().pushMessage(
    "Success:", f"Saved all images for {city}", level=3, duration=5
)
