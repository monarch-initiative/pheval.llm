# Provide a list of json filenames in a txt file and a directory with these files
import os
import json
import pandas as pd
import re
from pathlib import Path

# --- Configuration ---
jsonfilenames_list_path = "leakage_experiment/SUPERCORRECT_ppkts_after_2023-10-31.txt"
jsondir = Path("/Users/leonardo/data/4917_poly_ppkts/cohortdir/jsons")
hpoa_path = Path.home() / "data" / "phenotype.hpoa"
output_csv_file = "disease_data_with_biocuration_date.tsv"

# --- Step 1: Extract data from JSON files into a list of dictionaries ---
extracted_data = []
print("Starting data extraction from JSON files...")
with open(jsonfilenames_list_path, "r") as f:
    for line in f:
        filename = line.strip()

        jsonfile = jsondir / filename

        if not jsonfile.exists():
            print(f"Warning: File not found, skipping: {jsonfile}")
            continue

        with open(jsonfile, "r") as jf:
            try:
                data = json.load(jf)
                diseases = data.get("diseases", [])
                if not diseases:
                    extracted_data.append(
                        {"json_filename": filename, "disease_id": "N/A", "disease_label": "N/A"}
                    )
                else:
                    for disease in diseases:
                        term = disease.get("term", {})
                        extracted_data.append(
                            {
                                "json_filename": filename,
                                "disease_id": term.get("id"),
                                "disease_label": term.get("label"),
                            }
                        )
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from file, skipping: {jsonfile}")

# Create the main DataFrame
main_df = pd.DataFrame(extracted_data)
print(f"Successfully created initial DataFrame with {len(main_df)} rows.")

# --- Step 2: Read the HPOA file and prepare it ---
print(f"Reading HPOA file from: {hpoa_path}")
if not hpoa_path.exists():
    raise FileNotFoundError(f"HPOA file not found at the specified path: {hpoa_path}")

hpoa_df = pd.read_csv(hpoa_path, comment="#", sep="\t")
# We only need the database_id and biocuration columns
hpoa_df = hpoa_df[["database_id", "biocuration"]].dropna()

# --- Step 3: Create a mapping from OMIM ID to the earliest biocuration date ---
print("Processing HPOA data to find earliest biocuration dates...")


# Helper function to parse dates from the biocuration string
def find_earliest_date(biocuration_series):
    all_dates = []
    date_pattern = re.compile(r"\[(\d{4}-\d{2}-\d{2})\]")
    for entry in biocuration_series:
        found_dates = date_pattern.findall(entry)
        all_dates.extend(found_dates)
    if not all_dates:
        return pd.NaT  # Return 'Not a Time' if no dates are found
    # Convert string dates to datetime objects and find the minimum
    return min(pd.to_datetime(d) for d in all_dates)


# Group by disease ID and apply the function to find the earliest date for each
earliest_dates_map = hpoa_df.groupby("database_id")["biocuration"].apply(find_earliest_date)

# --- Step 4: Add the new column to the main DataFrame ---
print("Mapping earliest dates to the main DataFrame...")
main_df["earliest_biocuration_date"] = main_df["disease_id"].map(earliest_dates_map)

# --- Step 5: Save the final, updated DataFrame to a TSV file ---
main_df.to_csv(output_csv_file, index=False, sep="\t")
print(f"Data processing complete. Results saved to {output_csv_file}")
print("\nFinal DataFrame head:")
print(main_df.head())
