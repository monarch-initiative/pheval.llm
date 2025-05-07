# Main Analysis of output
from pathlib import Path
import math
import pandas as pd
from scipy.stats import chi2_contingency as chi
from scipy.stats import kruskal 
from malco.post_process.df_save_util import safe_save_tsv
from malco.post_process.generate_plots import make_plots

# MALCO langs check output.
# If grounding fails number is not too different across languages, we could use

data_dir = Path("/Users/leonardo/git/malco/out_multlingual_nov24/multilingual/rank_data")

# To run subsets of phenopackets, run 
#data_dir = Path("/Users/leonardo/git/malco/multout_pyboqa/rank_data")
comparing = "language"
topn_file_name = "topn_result.tsv"
topn_file = data_dir / topn_file_name
mrr_file = data_dir / "mrr_result.tsv"
languages = ["en", "es", "cs", "tr", "de", "it", "zh", "nl", "ja"]

"""
#+++++++++++++++++++++++++++++++++++++
# MRR test
mrr_results = {}
samples = {}
for lang in languages:
    fulldf_path = Path(f"/Users/leonardo/git/malco/multout_pyboqa/{lang}/full_df_results.tsv")
    #fulldf_path = Path(f"/Users/leonardo/git/malco/out_multlingual_nov24/multilingual/{lang}/full_df_results.tsv")
    df_onelang = pd.read_csv(fulldf_path, delimiter="\t")
    mrr = df_onelang.groupby("label")["reciprocal_rank"].max()
    std = mrr.std()
    mrr_results[lang] = [mrr.mean(), std, std/math.sqrt(len(df_onelang.groupby("label")))]
    ranks = mrr.apply(lambda x: 1/x if x>0.05 else 11)
    samples[lang] = ranks.tolist()

print(mrr_results)
#+++++++++++++++++++++++++++++++++++++
# Now what? Need some CI and some test, I guess, but which one? TODO
# Chi2 is for categorical, not cardinal data! --> use Kruskal Wallis test

kr_correct = kruskal(*samples.values(), axis = 0) 
"""
#+++++++++++++++++++++++++++++++++++++
"""df_test = pd.DataFrame()
df_test['language'] = df['language']
df_test['rank1'] = df["n1"]
df_test['rank2n3'] = df["n2"]+df["n3"]
df_test['rank4n5'] = df["n4"]+df["n5"]
df_test['rank46o10'] = df["n6"]+df["n7"]+df["n8"]+df["n9"]+df["n10"]
#df_test['rank4to10'] =df["n4"]+df["n5"] + df["n6"]+df["n7"]+df["n8"]+df["n9"]+df["n10"]
#df_test['not'] =  df["n4"]+df["n5"]+ df["n6"]+df["n7"]+df["n8"]+df["n9"]+df["n10"] +df["nf"]+df['grounding_failed']
df_test['not'] = df["nf"]+df['grounding_failed']
last = 6
kruskal_groups = [df_test.iloc[0,1:last].to_numpy().tolist(),
                df_test.iloc[1,1:last].to_numpy().tolist(),
                df_test.iloc[2,1:last].to_numpy().tolist(),
                df_test.iloc[3,1:last].to_numpy().tolist(),
                df_test.iloc[4,1:last].to_numpy().tolist(),
                df_test.iloc[5,1:last].to_numpy().tolist(),
                df_test.iloc[6,1:last].to_numpy().tolist(),
                df_test.iloc[7,1:last].to_numpy().tolist(),
                df_test.iloc[8,1:last].to_numpy().tolist(),]

kr_res = kruskal(*kruskal_groups, axis = 0) # need to assign nf to, say, 50 (or 4500 or whateva)
print(kr_res)"""

#+++++++++++++++++++++++++++++++++++++
# TODO add strict scoring here?
df = pd.read_csv(topn_file, delimiter="\t")

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
