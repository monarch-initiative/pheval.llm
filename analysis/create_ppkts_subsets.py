"""This python script imports phenopackets from a directory and creates subsets based on the
number of observed HPO terms that they contain."""

import os
import sys
import json

input_path = sys.argv[1] if len(sys.argv) > 1 else "data/phenopackets/"

# import all json files in the given directory and subdirectories
phenopackets = []
for root, dirs, files in os.walk(input_path):
    for filename in files:
        if filename.endswith(".json"):
            with open(os.path.join(root, filename), "r") as f:
                pkt_data = json.load(f)
                pkt_data["_filename"] = filename  # Store the original filename
                phenopackets.append(pkt_data)

# create subsets based on the number of observed HPO terms
# Subsets bin between 0 and 1 HPOs, between 2 and 5, between 6 and 10, between 11 and 20, between 21 and 50, more than 50
# observed HPOs in the json are in the list of "phenotypicFeatures", whenever the item does not contain an "excluded" field

hpo_bins = {
    "0-1": [],
    "2-5": [],
    "6-10": [],
    "11-20": [],
    "21-50": [],
    "50+": [],
}

for pkt in phenopackets:
    hpo_count = sum(1 for feature in pkt.get("phenotypicFeatures", []) if "excluded" not in feature)
    if hpo_count == 0:
        hpo_bins["0-1"].append(pkt)
    elif 1 < hpo_count <= 5:
        hpo_bins["2-5"].append(pkt)
    elif 5 < hpo_count <= 10:
        hpo_bins["6-10"].append(pkt)
    elif 10 < hpo_count <= 20:
        hpo_bins["11-20"].append(pkt)
    elif 20 < hpo_count <= 50:
        hpo_bins["21-50"].append(pkt)
    else:
        hpo_bins["50+"].append(pkt)

# print the number of phenopackets in each subset
for bin_range, pkts in hpo_bins.items():
    print(f"Phenopackets with {bin_range} observed HPO terms: {len(pkts)}")

# write the json file names for each subset into a separate text file
# create output directory if it does not exist, containing all of these files
output_dir = "analysis_out/phenopacket_subsets/nHPO/"
os.makedirs(output_dir, exist_ok=True)

for bin_range, pkts in hpo_bins.items():
    with open(os.path.join(output_dir, f"phenopackets_{bin_range}.txt"), "w") as f:
        for pkt in pkts:
            f.write(f"{pkt.get('_filename', 'unknown')}\n")
