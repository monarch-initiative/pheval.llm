"""Kruskal-Wallis test script for MALCO multilingual output.
ADD DESCRIPTION HERE. TODO IMPORTANT!
Works on individual data points..."""

from pathlib import Path

import pandas as pd
from scipy.stats import kruskal

# MALCO langs check output.
languages = ["en", "es", "cs", "tr", "de", "it", "zh", "nl", "ja", "fr"]

# MRR data for test
mrr_results = {}
samples = {}
for lang in languages:

    # fulldf_path = Path(f"/Users/leonardo/git/malco/final_multilingual_output/{lang}/full_df_results.tsv")
    # Repackaging format:
    fulldf_path = Path(
        f"data/results/multilingual_main/full_results/full_df_{lang}-Meditron3_70b.tsv"
    )
    # mrr = df_onelang.groupby("label")["reciprocal_rank"].max()
    # Repackaging format:
    df_onelang = pd.read_csv(fulldf_path, delimiter="\t", usecols=["scored"])
    df_scored_dict = df_onelang["scored"].apply(ast.literal_eval)
    # mrr = df_onelang.groupby("label")["reciprocal_rank"].max()
    # std = mrr.std()
    # mrr_results[lang] = [mrr.mean(), std, std/math.sqrt(len(df_onelang.groupby("label")))]
    # ranks = mrr.apply(lambda x: 1/x if x>0.099 else 11)

    # Repackaging format:
    # For each line in the scored column, if in that list of dicts any of the dicts' field "is_correct" is True,
    # then assign the content of the field 'rank', transformed to float, to ranks.
    ranks = df_scored_dict.apply(lambda x: [float(d["rank"]) for d in x if d["is_correct"]])
    # If no dict in the list has 'is_correct' True, assign 11 to ranks.
    ranks = ranks.apply(lambda x: x[0] if x else 11)
    # ranks = df_scored_dict.apply(lambda x: 1/x if x>0.099 else 11)

    samples[lang] = ranks.tolist()

# print(mrr_results)
# Chi2 is for categorical, not cardinal data! --> use Kruskal Wallis test

kr_correct = kruskal(*samples.values(), axis=0)
print("\n\nKruskal-Wallis test result:", kr_correct)
