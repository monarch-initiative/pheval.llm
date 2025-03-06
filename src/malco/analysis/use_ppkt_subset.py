import re
import pandas as pd
import numpy as np
from pathlib import Path
from malco.post_process.df_save_util import safe_save_tsv

#==============================================================================
# Change the following paths to match your system and subset of phenopacket IDs

# output directory for the results of this script
output_dir = Path("/Users/leonardo/git/malco/multout_pyboqa")

# BOQA subset by Peter Hansen, cases where BOQA got the right answer
# Any txt file with a list of phenopacket IDs will do
ppktids_filen = "/Users/leonardo/data/phenopacket_ids_boqa_rank1.txt"

#==============================================================================
# Function to replace all non-word characters with underscores
def modify_filename(ppktID):
    modified_name = re.sub(r'[^\w]', '_', ppktID) + "_en-prompt.txt"
    return modified_name



with open(ppktids_filen, "r") as f:
    ppktids = f.readlines()
    ppktids = [x.strip() for x in ppktids]
    ppktids = [modify_filename(x) for x in ppktids]

languages = ["en", "es", "cs", "tr", "de", "it", "zh", "nl", "ja"]
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

rank_df = pd.DataFrame(0, index=np.arange(9), columns=header) # HARDCODED 9!!!

    
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
    fulldf = fulldf[fulldf["label"].isin(ppktids)]
    
    # save full_df too a new file in multout_pyboqa
    full_df_path = output_dir / lang

    full_df_filename = "full_df_results.tsv"
    safe_save_tsv(full_df_path, full_df_filename, fulldf)
    
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