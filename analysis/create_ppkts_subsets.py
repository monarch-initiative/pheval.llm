"""This python script imports phenopackets from a directory and creates subsets based on the
number of observed HPO terms that they contain. Configuration is loaded from a YAML file."""

import os
import sys
import json
import yaml
from pathlib import Path

# Get script directory to find config file
script_dir = Path(__file__).parent
config_file = script_dir / "phenopacket_subset_config.yaml"

# Load configuration
with open(config_file, "r") as f:
    config = yaml.safe_load(f)

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

# Create bins based on configuration
hpo_bins = {bin_config["name"]: [] for bin_config in config["bins"]}

for pkt in phenopackets:
    hpo_count = sum(1 for feature in pkt.get("phenotypicFeatures", []) if "excluded" not in feature)

    # Find which bin this phenopacket belongs to
    for bin_config in config["bins"]:
        min_hpos = bin_config["min_hpos"]
        max_hpos = bin_config["max_hpos"]

        if max_hpos is None:  # No upper limit
            if hpo_count >= min_hpos:
                hpo_bins[bin_config["name"]].append(pkt)
                break
        else:  # Has upper limit
            if min_hpos <= hpo_count <= max_hpos:
                hpo_bins[bin_config["name"]].append(pkt)
                break

# print the number of phenopackets in each subset
for bin_name, pkts in hpo_bins.items():
    print(f"Phenopackets in bin '{bin_name}': {len(pkts)}")

# Create output directory based on config
output_config = config["output"]
output_dir = os.path.join(output_config["base_dir"], output_config["config_name"])
os.makedirs(output_dir, exist_ok=True)

print(f"Writing subset files to: {output_dir}")

# Write the json file names for each subset into a separate text file
for bin_name, pkts in hpo_bins.items():
    filename = f"{output_config['file_prefix']}_{bin_name}{output_config['file_extension']}"
    with open(os.path.join(output_dir, filename), "w") as f:
        for pkt in pkts:
            f.write(f"{pkt.get('_filename', 'unknown')}\n")
