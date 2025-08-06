# read in results.yaml, look at all those without named_entities,
# extracted_object[label] unique, have a look

import pandas as pd
import regex as re

# import yaml file at /Users/leonardo/git/malco/out_multlingual_nov24/raw_results/multilingual/ja/results.yaml
import yaml

with open(
    "/Users/leonardo/git/malco/out_multlingual_nov24/raw_results/multilingual/ja/results.yaml", "r"
) as file:
    data = list(yaml.safe_load_all(file.read()))

# iterate over all results and check if named_entities field exists, if not,
# save the content of the "label" subfield of the "extracted_object" field in a dataframe, together with the "input_text" field

# Initialize an empty list to store the results
success = []
no_success = []

# Iterate over all results
for result in data:
    # Check if 'named_entities' field exists
    label = result.get("extracted_object", {}).get("label", None)
    input_text = result.get("input_text", None)

    if "named_entities" not in result:
        if label and input_text:
            no_success.append({"label": label, "input_text": input_text})

    if "named_entities" in result:
        success.append({"label": label, "input_text": input_text})
        # Save the 'label' subfield of 'extracted_object' and 'input_text' field
# Convert the results to a DataFrame
df_s = pd.DataFrame(success)
df_ns = pd.DataFrame(no_success)

# Remove items with the same label present in both df_s and df_ns from df_ns
df_ns = df_ns[~df_ns["label"].isin(df_s["label"])]
unique_labels = df_ns["label"].unique()
input_texts = [df_ns[df_ns["label"] == label]["input_text"].values[0] for label in unique_labels]
trimmed_labels = [label[:-14] for label in unique_labels]
# trimmed_labels = [label.replace('_.json', '.json') for label in trimmed_labels]

ns_unique = pd.DataFrame(
    {"label": unique_labels, "input_text": input_texts, "ppkt_filename": trimmed_labels}
)

# Traverse all ppkt_filename and look for matching files in subdirectories of /Users/leonardo/data/phenopacket-store
# If a match is found load the json file and extract the 'phenotypicFeatures' field
import json
import os
import re

# Directory to search
search_directory = "/Users/leonardo/data/phenopacket-store"

# Dictionary to store the modified filenames
filename_dict = {}


# Function to replace all non-word characters with underscores
def modify_filename(ppktID):
    modified_name = re.sub(r"[^\w]", "_", ppktID)
    return modified_name + ".json"


# Traverse the directory and subdirectories
for root, _, files in os.walk(search_directory):
    for file in files:
        if file.endswith(".json"):
            ppktID = json.load(open(os.path.join(root, file)))["id"]
            modified_filename = modify_filename(ppktID)
            filename_dict[modified_filename] = os.path.join(root, file)

# List to store the extracted phenotypicFeatures
phenotypic_features_list = []

# Traverse all ppkt_filename and look for matching files
for filename in ns_unique["ppkt_filename"]:
    fn = filename + ".json"
    if fn in filename_dict:
        json_file_path = filename_dict[fn]
        with open(json_file_path, "r") as file:
            data = json.load(file)
            phenotypic_features = data.get("phenotypicFeatures", [])
            type_count = 0
            excluded_type_count = 0
            for feature in phenotypic_features:
                if "type" in feature:
                    type_count += 1
                    if "excluded" in feature:
                        excluded_type_count += 1
            type_count = type_count - excluded_type_count
            phenotypic_features_list.append(
                {
                    "ppkt_filename": filename,
                    "type_count": type_count,
                    "excluded_type_count": excluded_type_count,
                }
            )


# Convert the phenotypic features list to a DataFrame
df_phenotypic_features = pd.DataFrame(phenotypic_features_list)

print(df_phenotypic_features[["type_count", "excluded_type_count"]].value_counts())
