from qgis.core import QgsLayoutExporter, QgsProject


def export_map_to_image(
    project_file, layout_name, output_file, image_format="PNG", output_dpi=300
):
    # Step 1: Load the QGIS project
    project = QgsProject.instance()
    project.read(project_file)

    # Step 2: Get the map layout
    layout_manager = project.layoutManager()
    layout = layout_manager.layoutByName(layout_name)

    if layout is None:
        print(f"Layout '{layout_name}' not found in the project.")
        return

    # Step 3: Configure map settings
    exporter = QgsLayoutExporter(layout)
    ms = QgsMapSettings()
    ms.setFromLayout(layout)
    ms.setOutputSize(
        layout.page().layoutUnits(),
        layout.page().pageSize(),
        layout.page().renderUnits(),
    )

    # Set other map settings if needed
    # ms.setOutputDpi(output_dpi)
    # ms.setExtent(QgsRectangle(x_min, y_min, x_max, y_max))

    # Step 4: Export the layout to an image
    image_settings = QgsLayoutExporter.ImageExportSettings()
    image_settings.dpi = output_dpi
    image_settings.exportDpi = output_dpi
    image_settings.imageSize = ms.size()
    image_settings.imageWidth = ms.width()
    image_settings.imageHeight = ms.height()
    image_settings.imageExtent = ms.extent()
    image_settings.resolution = output_dpi
    image_settings.scale = ms.scale()
    image_settings.worldFile = False

    try:
        exporter.exportToImage(output_file, image_settings)
    except:
        raise

    print(f"Map exported to {output_file} successfully.")


if __name__ == "__main__":
    # Provide the paths and names accordingly
    project_file_path = "../data/3_QGIS/Los Angeles.qgz"
    layout_name_to_export = "Overview"
    output_image_file = "../figs/Los Angeles/new_image.png"
    output_dpi = 300

    export_map_to_image(
        project_file_path, layout_name_to_export, output_image_file, "PNG", output_dpi
    )
