# Main Analysis of output
import pandas as pd 
from pathlib import Path 
from malco.post_process.df_save_util import safe_save_tsv
from malco.post_process.generate_plots import make_plots

# MALCO langs check output. 
# If grounding fails number is not too different across languages, we could use
# v

data_dir = Path("/Users/leonardo/git/malco/out_multlingual_nov24/multilingual/rank_data")
comparing = "language"
topn_file_name = "topn_result.tsv"
topn_file = data_dir / topn_file_name
mrr_file = data_dir / "mrr_result.tsv"

df = pd.read_csv(topn_file, delimiter="\t")
#TODO add strict scoring here
#valid_cases = df["num_cases"] - df["grounding_failed"]
valid_cases = df["num_cases"]
df["top1"] = (df["n1"]) / valid_cases
df["top3"] = (df["n1"] + df["n2"] + df["n3"]) / valid_cases
df["top5"] = (df["n1"] + df["n2"] + df["n3"] + df["n4"] + df["n5"]) / valid_cases
df["top10"] = (
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
) / valid_cases
df["not_found"] = (df["nf"] + df["grounding_failed"]) / valid_cases

df_aggr = pd.DataFrame()
df_aggr = pd.melt(
    df,
    id_vars=comparing,
    value_vars=["top1", "top3", "top5", "top10", "not_found"],
    var_name="Rank_in",
    value_name="percentage",
)

# If "topn_aggr.tsv" already exists, prepend "old_"
# It's the user's responsibility to know only up to 2 versions can exist, then data is lost
topn_aggr_file_name = "topn_aggr.tsv"
topn_aggr_file = data_dir / topn_aggr_file_name
safe_save_tsv(data_dir, topn_aggr_file_name, df_aggr)

languages = ["en","es","cs","tr","de","it","zh","nl"]

num_ppkt = {}
for lang in languages:
    num_ppkt[lang] = df[df[comparing]==lang]['num_cases'].iloc[0]

models = "USELESS FOR LANGUAGES" # !

make_plots(
            mrr_file,
            data_dir,
            languages,
            num_ppkt,
            models,
            topn_aggr_file,
            comparing,
        )