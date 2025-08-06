"""
As some exploratory data analysis, let us divide the set into two and look for
some properties. Meanwhile, create dictonary: {ppkt_name : [rank, date]}.

Needs model name as input, e.g. run as:

>>> python src/malco/analysis/time_ic/rank_date_exploratory.py gpt-4o

Some output will be printed (TODO document) to terminal. Most importantly, it generates (TODO add model name in pickle file name):
`rank_date_dict.pkl`
which is needed for running

>>> python src/malco/analysis/time_ic/diseases_avail_knowledge.py gpt-4o
"""

import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Parse user input and set paths:
model = str(sys.argv[1])
ranking_results_filename = f"out_openAI_models/multimodel/{model}/full_df_results.tsv"
data_dir = Path.home() / "data"
hpoa_file_path = data_dir / "phenotype.hpoa"
outdir = Path.cwd() / "src" / "malco" / "analysis" / "time_ic"


# (1) HPOA for dates
# HPOA import and setup
hpoa_df = pd.read_csv(
    hpoa_file_path,
    sep="\t",
    header=4,
    low_memory=False,  # Necessary to suppress Warning we don't care about
)

labels_to_drop = [
    "disease_name",
    "qualifier",
    "hpo_id",
    "reference",
    "evidence",
    "onset",
    "frequency",
    "sex",
    "modifier",
    "aspect",
]
hpoa_df = hpoa_df.drop(columns=labels_to_drop)

hpoa_df["date"] = hpoa_df["biocuration"].str.extract(r"\[(.*?)\]")
hpoa_df = hpoa_df.drop(columns="biocuration")
hpoa_df = hpoa_df[hpoa_df["database_id"].str.startswith("OMIM")]

hpoa_unique = hpoa_df.groupby("database_id").date.min()
# Now length 8251, and e.g. hpoa_unique.loc["OMIM:620662"] -> '2024-04-15'


# import df of LLM results
rank_results_df = pd.read_csv(ranking_results_filename, sep="\t")


# Go through results data and make set of found vs not found diseases.
found_diseases = []
not_found_diseases = []
rank_date_dict = {}
ppkts = rank_results_df.groupby("label")[["term", "correct_term", "is_correct", "rank"]]
for ppkt in ppkts:  # TODO 1st for ppkt in ppkts
    # ppkt is tuple ("filename", dataframe) --> ppkt[1] is a dataframe
    disease = ppkt[1].iloc[0]["correct_term"]

    if any(ppkt[1]["is_correct"]):
        found_diseases.append(disease)
        index_of_match = ppkt[1]["is_correct"].to_list().index(True)
        try:
            rank = ppkt[1].iloc[index_of_match]["rank"]  # inverse rank does not work well
            rank_date_dict[ppkt[0]] = [
                rank.item(),
                hpoa_unique.loc[ppkt[1].iloc[0]["correct_term"]],
            ]
            # If ppkt[1].iloc[0]["correct_term"] is nan, then KeyError "e" is nan
        except (ValueError, KeyError) as e:
            print(f"Error {e} for {ppkt[0]}, disease {ppkt[1].iloc[0]['correct_term']}.")

    else:
        not_found_diseases.append(disease)
        try:
            rank_date_dict[ppkt[0]] = [None, hpoa_unique.loc[ppkt[1].iloc[0]["correct_term"]]]
        except (ValueError, KeyError) as e:
            # pass
            # TODO collect the below somewhere
            print(f"Error {e} for {ppkt[0]}, disease {ppkt[1].iloc[0]['correct_term']}.")

# gpt-4o output, reasonable enough to throw out 62 cases ~1%. 3 OMIMs to check and 3 nan
# TODO clean up here
# len(rank_date_dict) --> 6625
# len(ppkts) --> 6687

with open(outdir / "rank_date_dict.pkl", "wb") as f:
    pickle.dump(rank_date_dict, f)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Analysis of found vs not-found TODO cleanup
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
found_set = set(found_diseases)
notfound_set = set(not_found_diseases)
all_set = found_set | notfound_set
# len(all_set) --> 476

# compute the overlap of found vs not-found disesases
overlap = []

for i in found_set:
    if i in notfound_set:
        overlap.append(i)

print(f"Number of found diseases by {model} is {len(found_set)}.")
print(f"Number of not found diseases by {model} is {len(notfound_set)}.")
print(f"Diseases sometimes found, sometimes not, by {model} are {len(overlap)}.\n")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Look at the 263-129 (gpt-4o) found diseases not present in not-found set ("always found")
# and the opposite namely "never found" diseases. Average date of two sets is?

always_found = found_set - notfound_set  # 134
never_found = notfound_set - found_set  # 213
# meaning 347/476, 27% sometimes found sometimes not, 28% always found, 45% never found.

# Compute average date of always vs never found diseases
results_dict = {}  # turns out being 281 long

# TODO get rid of next line, bzw hpoa_unique does not work for loop below
hpoa_df.drop_duplicates(subset="database_id", inplace=True)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
for af in always_found:
    try:
        results_dict[af] = [True, hpoa_df.loc[hpoa_df["database_id"] == af, "date"].item()]
        # results_dict[af] = [True, hpoa_unique.loc[hpoa_unique['database_id'] == af, 'date'].item() ]
    except ValueError:
        print(f"No HPOA in always_found for {af}.")

for nf in never_found:
    try:
        results_dict[nf] = [False, hpoa_df.loc[hpoa_df["database_id"] == nf, "date"].item()]
        # results_dict[nf] = [False, hpoa_unique.loc[hpoa_unique['database_id'] == nf, 'date'].item() ]
    except ValueError:
        print(f"No HPOA in never_found for {nf}.")

# TODO No HPOA for ... comes from for ppkt in ppkts, then
#    disease = ppkt[1].iloc[0]['correct_term']
res_to_clean = pd.DataFrame.from_dict(results_dict).transpose()
res_to_clean.columns = ["found", "date"]
res_to_clean["date"] = pd.to_datetime(res_to_clean.date).values.astype(np.int64)
final_avg = pd.DataFrame(pd.to_datetime(res_to_clean.groupby("found").mean()["date"]))
print(final_avg)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
