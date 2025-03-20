# Main Analysis of output
from pathlib import Path

import pandas as pd

from malco.io.reading import safe_save_tsv
from malco.process.generate_plots import make_plots

# MALCO langs check output.
# If grounding fails number is not too different across languages, we could use
# v

data_dir = Path("/Users/leonardo/git/malco/out_multlingual_nov24/multilingual/rank_data")
comparing = "language"
topn_file_name = "topn_result.tsv"
topn_file = data_dir / topn_file_name
mrr_file = data_dir / "mrr_result.tsv"

df = pd.read_csv(topn_file, delimiter="\t")
# TODO add strict scoring here
# valid_cases = df["num_cases"] - df["grounding_failed"]
valid_cases = df["num_cases"]
df["Top-1"] = 100 * (df["n1"]) / valid_cases
df["Top-3"] = 100 * (df["n1"] + df["n2"] + df["n3"]) / valid_cases
df["Top-5"] = 100 * (df["n1"] + df["n2"] + df["n3"] + df["n4"] + df["n5"]) / valid_cases
df["Top-10"] = (
    100
    * (
        df["n1"]
        + df["n2"]
        + df["n3"]
        + df["n4"]
        + df["n5"]
        + df["n6"]
        + df["n7"]
        + df["n8"]
        + df["n9"]
        + df["n10"]
    )
    / valid_cases
)
df["Not Found"] = 100 * (df["nf"] + df["grounding_failed"]) / valid_cases

df_aggr = pd.DataFrame()
df_aggr = pd.melt(
    df,
    id_vars=comparing,
    value_vars=["Top-1", "Top-3", "Top-5", "Top-10", "Not Found"],
    var_name="Rank_in",
    value_name="percentage",
)


# If "topn_aggr.tsv" already exists, prepend "old_"
# It's the user's responsibility to know only up to 2 versions can exist, then data is lost
topn_aggr_file_name = "topn_aggr.tsv"
topn_aggr_file = data_dir / topn_aggr_file_name
safe_save_tsv(data_dir, topn_aggr_file_name, df_aggr)

languages = ["en", "es", "cs", "tr", "de", "it", "zh", "nl"]

num_ppkt = {}
for lang in languages:
    num_ppkt[lang] = df[df[comparing] == lang]["num_cases"].iloc[0]

models = "USELESS FOR LANGUAGES"  # !

make_plots(
    mrr_file,
    data_dir,
    languages,
    num_ppkt,
    models,
    topn_aggr_file,
    comparing,
)
