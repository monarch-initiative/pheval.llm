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
            file_path = os.path.join(root, filename)
            with open(file_path, "r") as f:
                pkt_data = json.load(f)
                pkt_data["_filename"] = filename  # Store the original filename
                pkt_data["_absolute_path"] = os.path.abspath(file_path)  # Store absolute path
                phenopackets.append(pkt_data)

# Create output directory based on config
output_config = config["output"]
output_dir = os.path.join(output_config["base_dir"], output_config["config_name"])
os.makedirs(output_dir, exist_ok=True)
    
# ----------- HPO BINS -----------
# Create bins based on configuration
if False:
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


    # Write the json file absolute paths for each subset into a separate text file
    write = False
    if write:
        print(f"Writing subset files to: {output_dir}")
        for bin_name, pkts in hpo_bins.items():
            filename = f"{output_config['file_prefix']}_{bin_name}{output_config['file_extension']}"
            with open(os.path.join(output_dir, filename), "w") as f:
                for pkt in pkts:
                    f.write(f"{pkt.get('_absolute_path', 'unknown')}\n")

# ----------- DISEASE CATEGORIES -----------
# This part creates subsets based on disease categories using HPO
import hpotk
from tqdm import tqdm
store = hpotk.configure_ontology_store()
hpo = store.load_hpo()

HEART = hpo.get_term("HP:0001626")  #  Abnormality of the cardiovascular system
BRAIN = hpo.get_term("HP:0000707")  # Abnormality of the nervous system
IMMUNE = hpo.get_term("HP:0002715")  # Abnormality of the immune system

disease_categories = {"cardiovascular": [], "neurological": [], "immunological": []}
pkt_to_file = {pkt["id"]: pkt.get("_absolute_path", "unknown") for pkt in phenopackets}
for pkt in tqdm(phenopackets, total=len(phenopackets)):
    ppkt_observed_features = [
        feature for feature in pkt.get("phenotypicFeatures", []) if "excluded" not in feature
    ]
    for feature in ppkt_observed_features:
        term_id = feature.get("type", {}).get("id")
        if term_id:
            term = hpo.get_term(term_id)
            if term and hpo.graph.is_ancestor_of(HEART, term) and pkt["id"] not in disease_categories["cardiovascular"]:
                disease_categories["cardiovascular"].append(pkt["id"])
            if term and hpo.graph.is_ancestor_of(BRAIN, term) and pkt["id"] not in disease_categories["neurological"]:
                disease_categories["neurological"].append(pkt["id"])
            if term and hpo.graph.is_ancestor_of(IMMUNE, term) and pkt["id"] not in disease_categories["immunological"]:
                disease_categories["immunological"].append(pkt["id"])
# print the number of unique phenopackets in each disease category
for category, pkts in disease_categories.items():
    print(f"Phenopackets in disease category '{category}': {len(set(pkts))}")
# Print the size of the overlap between categories
cardiovascular_set = set(disease_categories["cardiovascular"])
neurological_set = set(disease_categories["neurological"])
immunological_set = set(disease_categories["immunological"])
print(f"Overlap between cardiovascular and neurological: {len(cardiovascular_set & neurological_set)}")
print(f"Overlap between cardiovascular and immunological: {len(cardiovascular_set & immunological_set)}")
print(f"Overlap between neurological and immunological: {len(neurological_set & immunological_set)}")
print(f"Overlap between all three: {len(cardiovascular_set & neurological_set & immunological_set)}")

"""
Phenopackets in bin '0-1': 432
Phenopackets in bin '2-5': 1532
Phenopackets in bin '6-10': 1777
Phenopackets in bin '11-20': 1239
Phenopackets in bin '21-50': 234
Phenopackets in bin '50p': 0
Phenopackets in disease category 'heart': 1042
Phenopackets in disease category 'brain': 3532
Phenopackets in disease category 'immune': 448
Overlap between heart and brain: 487
Overlap between heart and immune: 156
Overlap between brain and immune: 292
Overlap between all three: 100
"""
# write the phenopacket json paths for each disease category into a separate text file
write = True
if write:
    print(f"Writing disease category files to: {output_dir}")
    for category, pkts in disease_categories.items():
        filename = f"{output_config['file_prefix']}_{category}{output_config['file_extension']}"
        with open(os.path.join(output_dir, filename), "w") as f:
            for pkt in pkts:
                f.write(f"{pkt_to_file.get(pkt, 'unknown')}\n")