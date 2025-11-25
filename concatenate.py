"""
Concatenate all morphometrics into one CSV.
"""

import sys

import geopandas as gpd
import pandas as pd

import config


def get_last_modified_file(directory):
    files = [item for item in directory.iterdir() if item.is_file()]

    if not files:
        return None  # No subdirectories found

    sorted_files = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)

    return sorted_files[0].name


morpho_folder = config.MORPHOMETRICS_DIR
csv_folder = config.CSV_DIR
out_csv = csv_folder / "Morphometrics.csv"

df = pd.read_csv(out_csv)

print("The last version of Morphometrics.csv has", df["city"].nunique(), "cities.")


last_modified_file = get_last_modified_file(morpho_folder)
print("The last modified file is:", last_modified_file)

user_input = input(
    "Do you wish to concatenate all morphometrics files and overwrite "
    "Morphometrics.csv? (y/n) "
)

if user_input.lower() != "y":
    print("Exiting.")
    sys.exit(0)


print("Concatenating morphometrics files...")
# if df["city"].nunique() > len(city_list):
#     logger.info("CSV exists and has more cities. Skipping.")
#     return

df_full = pd.DataFrame()
for file in morpho_folder.iterdir():
    if " - morpho.gpkg" in file.name:
        city_name = file.stem.split(" - morpho")[0].strip()
        gdf = gpd.read_file(file)
        gdf["city"] = city_name
        df_full = pd.concat([df_full, gdf])

# Save
df_full.to_csv(str(out_csv), index=None)
# logger.info("CSV: Saved %s", out_csv)
print("Saved", out_csv)
