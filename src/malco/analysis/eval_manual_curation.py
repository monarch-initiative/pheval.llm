"""Import manually curated LLM replies and update the topn_result.tsv file in out_manual_curation"""

import pandas as pd
import os

rank_dir = "/Users/leonardo/git/malco/out_manual_curation/multilingual/rank_data/"
topn_file_name = rank_dir + "topn_result.tsv"
topn_file_out = rank_dir + "topn_result_curated.tsv"


cureated_file = "/Users/leonardo/git/malco/analysis_out/curated_replies_esitde.xlsx"

# Read the Excel file
rank_df = pd.read_excel(cureated_file)

# Extract columns G, H, I and set all -1 values to 0
rank_df = rank_df.iloc[:, 6:9].replace(-1, 0)
# Rename columns
rank_df.columns = ["it", "es", "de"]
# count different values in each column
counts = rank_df.value_counts()

it_counts = rank_df["it"].value_counts()
de_counts = rank_df["de"].value_counts()
es_counts = rank_df["es"].value_counts()


# Read the topn_result.tsv file
rank_df = pd.read_csv(topn_file_name, sep="\t")

rows_to_update = ["it_no_en", "es_no_en", "de_no_en"]
# Update the rows "it_no_en" and "de_no_en" in rank_df
rank_df.loc[rank_df["language"].isin(rows_to_update), rank_df.columns.difference(["language", "num_cases"])] = 0

for i in range(1, 11):
    try:
        rank_df.loc[rank_df["language"] == "it_no_en", f"n{i}"] = it_counts[i]
    except KeyError:
        pass
    try:
        rank_df.loc[rank_df["language"] == "es_no_en", f"n{i}"] = es_counts[i]
    except KeyError:
        pass
    try:
        rank_df.loc[rank_df["language"] == "de_no_en", f"n{i}"] = de_counts[i]
    except KeyError:
        pass

rank_df.loc[rank_df["language"] == "it_no_en", "nf"] = it_counts[0]
rank_df.loc[rank_df["language"] == "es_no_en", "nf"] = es_counts[0]
rank_df.loc[rank_df["language"] == "de_no_en", "nf"] = de_counts[0]

rank_df.to_csv(topn_file_out, sep="\t", index=False)

valid_cases = rank_df["num_cases"]
rank_df["Top-1"] = 100 * (rank_df["n1"]) / valid_cases
rank_df["Top-3"] = 100 * (rank_df["n1"] + rank_df["n2"] + rank_df["n3"]) / valid_cases
rank_df["Top-5"] = 100 * (rank_df["n1"] + rank_df["n2"] + rank_df["n3"] + rank_df["n4"] + rank_df["n5"]) / valid_cases
rank_df["Top-10"] = (
    100
    * (
        rank_df["n1"]
        + rank_df["n2"]
        + rank_df["n3"]
        + rank_df["n4"]
        + rank_df["n5"]
        + rank_df["n6"]
        + rank_df["n7"]
        + rank_df["n8"]
        + rank_df["n9"]
        + rank_df["n10"]
    )
    / valid_cases
)
rank_df["Not Found"] = 100 * (rank_df["nf"] + rank_df["grounding_failed"]) / valid_cases

df_aggr = pd.DataFrame()
df_aggr = pd.melt(
    rank_df,
    id_vars="language",
    value_vars=["Top-1", "Top-3", "Top-5", "Top-10", "Not Found"],
    var_name="Rank_in",
    value_name="percentage",
)

    # If "topn_aggr.tsv" already exists, prepend "old_"
    # It's the user's responsibility to know only up to 2 versions can exist, then data is lost
topn_aggr_file_name = "curated_topn_aggr.tsv"
topn_aggr_file = rank_dir + topn_aggr_file_name

df_aggr.to_csv(topn_aggr_file, sep="\t", index=False)

from pathlib import Path
from malco.post_process.generate_plots import make_plots
# Create dictinoary with the languages as key and num_cases as value
num_ppkt = {}
for lang in rank_df['language']:
    num_ppkt[lang] = rank_df.loc[rank_df['language'] == lang, 'num_cases'].values[0]

# Create the plots
make_plots("USELESS", Path(rank_dir), list(rank_df['language']), num_ppkt, "USELESS", topn_aggr_file, "language")