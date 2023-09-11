# Create GIS visualizations for selected cities

## Steps

For a given city, perform the following steps:

### 1. Get boundaries
- If the city is in the US, use the census tracts. Open QGIS and load census tracts of state from `data/0_boundaries/0_Census`. Select and save polygons for the city into a geopackage in `data/0_boundaries/[city]/[city].gpkg`.
- If the city is not in the US, get the boundaries from OSM. Add a list of cities into a text file and include the filepath in `config.py`. Then run `python run.py boundaries`. If the script fails to retrieve boundaries, download them directly from [Overpass Turbo](https://overpass-turbo.eu) and save them into `data/0_boundaries/[city]/[city].gpkg`.

If you use QGIS to edit the boundaries save the QGIS file into `data/3_QGIS/[city].qgz` for step 3.

### 2. Get buildings, streets and morphometrics
- Edit `config.py` and run the script with `python run.py` or any option described in the section `Docker` below. The output will be stored in `data/1_buildings_streets` and `data/2_morphometrics`.

### 3. Visualize in QGIS
- Load the boundaries in `data/0_boundaries/[city]/[city].gpkg` into QGIS and add a `Dark Matter (retina)` layer. Save the file into `data/3_QGIS/[city].qgz` if it does not exist.
- In the QGIS Python Editor, edit `city` in `0_load_layers.py` and run.
- Reclassify all layers: for each morphometrics layer, go to _Properties_>_Symbology_ and click _Delete All_, then _Classify_.
- Open map layout and check it looks good, set scale to round numbers.
- In the QGIS Python Editor, edit `city` in `1_export_images.py` and run. All images are exported into `figs/[city]/[city].jpg`.

## Docker

### Run the container
To use a docker image with all required packages:
```
make docker
```

### Run inside the container
To open a shell inside the container:
```
make shell
```
To run, edit `config.py` and run `python run.py` or add command line arguments.

### Run outside the container
Outside the container, edit `config.py` and run:
```
make run
make run cmd="'Buenos Aires'"
make run cmd="data/cities_us.txt start 'New York'"
```

## Command line arguments
You can use command line arguments directly to run a list of cities:
```
python run.py "New York" "Los Angeles"
```
You can also provide a text file and a starting point:
```
python run.py data/cities_us.txt start "New York"
```

## Tests

```
pytest
```

## Sources

New York City Boroughs: [NYC Open Data Portal](https://data.cityofnewyork.us/City-Government/Borough-Boundaries/tqmj-j8zm)
