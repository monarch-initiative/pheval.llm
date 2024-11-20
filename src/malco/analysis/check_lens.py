import sys

# from malco.post_process.post_process_results_format import read_raw_result_yaml
from pathlib import Path
from typing import List

import pandas as pd
import yaml


def read_raw_result_yaml(raw_result_path: Path) -> List[dict]:
    """
    Read the raw result file.

    Args:
        raw_result_path(Path): Path to the raw result file.

    Returns:
        dict: Contents of the raw result file.
    """
    with open(raw_result_path, "r") as raw_result:
        return list(
            yaml.safe_load_all(raw_result.read().replace("\x04", ""))
        )  # Load and convert to list


unique_ppkts = {}
# model=str(sys.argv[1])
models = ["gpt-3.5-turbo", "gpt-4-turbo", "gpt-4", "gpt-4o"]
for model in models:
    print("===" * 10, "\nEvaluating now: ", model, "\n" + "===" * 10)

    yamlfile = f"out_openAI_models/raw_results/multimodel/{model}/results.yaml"
    all_results = read_raw_result_yaml(yamlfile)

    counter = 0
    labelvec = []

    # Cannot have further files in raw_result_path!
    for this_result in all_results:
        extracted_object = this_result.get("extracted_object")
        if extracted_object:
            label = extracted_object.get("label")
            labelvec.append(label)
            terms = extracted_object.get("terms")
            if terms:
                counter += 1

    full_df_file = f"out_openAI_models/multimodel/{model}/results.tsv"
    df = pd.read_csv(full_df_file, sep="\t")
    num_ppkts = df["label"].nunique()
    unique_ppkts[model] = df["label"].unique()
    # The first should be equivalent to grepping "raw_" in some results.yaml
    print("The number of prompts that have something in results.yaml are: ", len(labelvec))
    print(
        "The number of prompts that have a non-empty differential (i.e. term is not None) is:",
        counter,
    )
    print(
        "The number of unique prompts/ppkts with a non-empty differential in results.tsv are:",
        num_ppkts,
        "\n",
    )

# This we know a posteriori, gpt-4o and gpt-4-turbo both have 5213 phenopackets
# Thus, let's print out what is missing in the others
for i in unique_ppkts["gpt-4-turbo"]:
    if i in unique_ppkts["gpt-4"]:
        continue
    else:
        print(f"Missing ppkt in gpt-4 is:\t", i)
print("\n")

for i in unique_ppkts["gpt-4-turbo"]:
    if i in unique_ppkts["gpt-3.5-turbo"]:
        continue
    else:
        print(f"Missing ppkt in gpt-3.5-turbo is:\t", i)
