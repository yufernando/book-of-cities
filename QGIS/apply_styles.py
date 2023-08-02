from pathlib import Path

root_folder = Path("/Users/fer/aretian-drive/Research/Book of Cities/")
project = QgsProject.instance()
root = project.layerTreeRoot()

def apply_styles():
    layer_name_list = [
        "Entropy", 
        "Fractal Dimension", 
        "Average Street Length",
        "Betweenness",
        "Building Area",
        "Building Compactness",
        "Buildings",
        "Streets"]


    for layer_name in layer_name_list:
        layer = project.mapLayersByName(layer_name)[0]
        layer.loadNamedStyle(str(root_folder / f"data/3_QGIS/styles/{layer_name}.qml"))
        layer.triggerRepaint()
        print("Applied style to", layer_name)
        
    
# Execute
apply_styles()


