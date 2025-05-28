import re
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
from malco.post_process.df_save_util import safe_save_tsv

#==============================================================================
# Change the following paths to match your system and subset of phenopacket IDs
# Subset of phenopackets after October 2023
#output_dir = Path("/Users/leonardo/git/malco/leakage_experiment")
#ppktids_filen = "/Users/leonardo/git/malco/ppkts_after_oct23_CORRECT.txt"

#TODO list of files in txt is the json file name, we have to take the id in thtat file and process it to get the prompt file name 


# Subset of 4917 phenopackets with French
output_dir = Path("/Users/leonardo/git/malco/final_multilingual_output")
ppktids_filen = "/Users/leonardo/git/malco/final_multilingual_output/ppkts_4917set.txt"

# Any txt file with a list of phenopacket IDs will do
#==============================================================================
# Function to replace all non-word characters with underscores
def modify_filename(ppktID, ppkt_dir):
    # If there is a ".json" extension, remove it
    if ppktID.endswith(".json"):
        # Copy 1 to 1 the code logic of phenopacket2prompt
        try:
            ppkt = json.loads(os.path.join(ppkt_dir, ppktID))
        except:
            print(f"Error loading JSON file: {ppktID}")
            return None
        ppktID = ppkt['id']
        modified_name = re.sub(r'[^\w]', '_', ppktID) + "_en-prompt.txt"
    else:
        modified_name = ppktID
    return modified_name

# Only used if we use the json file name
ppkt_dir = "/Users/leonardo/data/ppkts_4967_polyglot/jsons"

with open(ppktids_filen, "r") as f:
    ppktids = f.readlines()
    ppktids = [x.strip() for x in ppktids]
    ppktids = [modify_filename(x, ppkt_dir) for x in ppktids]
print("ppktids: ", len(ppktids))

languages = ["en", "es", "cs", "tr", "de", "it", "zh", "nl", "ja", "fr"]
comparing = "language"
header = [
        comparing,
        "n1",
        "n2",
        "n3",
        "n4",
        "n5",
        "n6",
        "n7",
        "n8",
        "n9",
        "n10",
        "n10p",
        "nf",
        "num_cases",
        "grounding_failed",  # and no correct reply elsewhere in the differential
    ]

rank_df = pd.DataFrame(0, index=np.arange(len(languages)), columns=header)

    
i=0
for lang in languages:
    # import full df for a given lang
    fulldf_path = Path(f"/Users/leonardo/git/malco/out_multlingual_nov24/multilingual/{lang}/full_df_results.tsv")
    fulldf = pd.read_csv(fulldf_path, sep="\t")

    # change ppktid to a given lang
    fulldf["label"] = fulldf["label"].str.replace(
                "_[a-z][a-z]-prompt", "_en-prompt", regex=True
            )

    # drop lines that are not in ppktids
    fulldf = fulldf[fulldf["label"].isin(ppktids)] # ISSUE HERE
    
    
    rank_df.loc[i, comparing] = lang

    ppkts = fulldf.groupby("label")[["term", "rank", "is_correct"]]

    # for each group
    for ppkt in ppkts:
        # is there a true? ppkt is tuple ("filename", dataframe) --> ppkt[1] is a dataframe
        if not any(ppkt[1]["is_correct"]):
            if all(ppkt[1]["term"].str.startswith("MONDO")):
                # no  --> increase nf = "not found"
                rank_df.loc[i, "nf"] += 1
            else:
                rank_df.loc[i, "grounding_failed"] += 1
        else:
            # yes --> what's it rank? It's <j>
            jind = ppkt[1].index[ppkt[1]["is_correct"]]
            j = int(ppkt[1]["rank"].loc[jind].values[0])
            if j < 11:
                # increase n<j>
                rank_df.loc[i, "n" + str(j)] += 1
            else:
                # increase n10p
                rank_df.loc[i, "n10p"] += 1
        rank_df.loc[i, "num_cases"] = len(ppkts)
    i = i +1

topn_file_name = "topn_result.tsv"

safe_save_tsv(output_dir / "rank_data", topn_file_name, rank_df)

# Now run main_analysis_multilingual.py adapting paths in there