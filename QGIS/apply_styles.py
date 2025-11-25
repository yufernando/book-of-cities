import sys
from pathlib import Path

# Add code directory to path to import config
# Assumes QGIS script is in code/QGIS/, so go up one level
code_dir = Path(__file__).resolve().parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

import config

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
        "Streets",
    ]

    for layer_name in layer_name_list:
        layer = project.mapLayersByName(layer_name)[0]
        layer.loadNamedStyle(
            str(config.QGIS_DATA_ROOT / f"3_QGIS/styles/{layer_name}.qml")
        )
        layer.triggerRepaint()
        print("Applied style to", layer_name)


# Execute
apply_styles()
