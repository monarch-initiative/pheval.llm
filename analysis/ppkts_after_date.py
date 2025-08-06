"""This script imports a list of PubMed IDs and their corresponding dates from a file,
then filters the PubMed IDs based on a cutoff date passed as input and saves the filtered
PubMed IDs to a new file.
"""

import datetime
import json
import os
import sys

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Check if the correct number of arguments is provided
if len(sys.argv) < 3:
    print("Usage: python ppkts_after_date.py <pmid2date_dict> <cutoff_date> [OPTIONAL <ppkts_dir>]")
    sys.exit(1)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Read the input file and load the PubMed IDs and their dates into a dictionary
input_file = str(sys.argv[1])
if not os.path.isfile(input_file):
    print(f"Error: The file {input_file} does not exist.")
    sys.exit(1)

with open(input_file, "r") as f:
    pmid2date_dict = json.load(f)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Check if the cutoff date is provided and parse it
cutoff_date = datetime.datetime.strptime(sys.argv[2], "%Y-%m-%d")

# Check if the cutoff date is valid
if cutoff_date > datetime.datetime.now():
    print("Error: The cutoff date cannot be in the future.")
    sys.exit(1)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Import the ppkts from the previous script
try:
    ppkts_dir = str(sys.argv[4])
except IndexError:
    ppkts_dir = "/Users/leonardo/data/ppkts_4967_polyglot/jsons"
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Iterate over all json files in the directory and populate a dictionary with as a key the filename and as a value the field .metaData.externalReferences
ppkts = {}
for filename in os.listdir(ppkts_dir):
    if filename.endswith(".json"):
        with open(os.path.join(ppkts_dir, filename), "r") as f:
            data = json.load(f)
            # Check if the key exists in the JSON data
            if "metaData" in data and "externalReferences" in data["metaData"]:
                ppkts[filename] = data["metaData"]["externalReferences"]
            else:
                print(f"Key not found in {filename}")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Go over pumbed_data which contains a datetime.datetime object and collect those received after cutoff_date in pubmeds_after_cutoff
pubmeds_after_cutoff = {}
for pmid, data in pmid2date_dict.items():
    # Extract only the date part (before the space)
    date_str = data["date"].split(" ")[0]
    pubmed_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    if pubmed_date > cutoff_date:
        pubmeds_after_cutoff[pmid] = data
        print(f"PMID: {pmid}, Date: {data['date']}")

new_ppkts = []
for fn, _ in ppkts.items():
    for id in pubmeds_after_cutoff.keys():
        str2search = id.replace(":", "_").strip()
        if str2search in fn:
            new_ppkts.append(fn)  # These are indeed json filenames

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Save the filtered PubMed IDs to a new file
output_file = (
    "ppkts_after_" + cutoff_date.strftime("%Y-%m-%d") + ".txt"
)  # Specify the output file name

with open(output_file, "w") as f:
    for item in new_ppkts:
        f.write(item + "\n")  # Write each item followed by a newline character

print(f"Saved {len(new_ppkts)} items to {output_file}")
