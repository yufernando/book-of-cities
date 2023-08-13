# Create GIS visualizations for selected cities

## Steps

For a given city, perform the following steps:

1. Create a QGIS file in `data/3_QGIS/[city].qgz`. Add a `Dark Matter (retina)` layer.
2. Load census tracts of state from the folder `data/0_boundaries/0_Census`. Select and save polygons for the city into a geopackage in `data/0_boundaries/[city]/[city].gpkg`.
3. In the `code/` folder, run `python run.py [city]`. The output will be stored in `data/1_buildings_streets` and `data/2_morphometrics`.
4. In the QGIS Python Editor, edit city in `0_load_layers.py` and run.
5. Reclassify all layers.
6. Open map layout and check it looks good.
7. In the QGIS Python Editor, edit city in `1_export_images.py` and run. All images are exported into `figs/[city]/[city].jpg`.

## Docker

To use a docker image with all required packages:
```
make jupyter
make shell
```

## Tests

```
pytest
```

## Sources

New York City Boroughs: [NYC Open Data Portal](https://data.cityofnewyork.us/City-Government/Borough-Boundaries/tqmj-j8zm)
