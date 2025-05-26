"""Kruskal-Wallis test script for MALCO multilingual output.
ADD DESCRIPTION HERE. TODO IMPORTANT!
Works on individual data points..."""

from pathlib import Path
import math
import pandas as pd
from scipy.stats import chi2_contingency as chi
from scipy.stats import kruskal 
from malco.post_process.df_save_util import safe_save_tsv
from malco.post_process.generate_plots import make_plots

# MALCO langs check output.
languages = ["en", "es", "cs", "tr", "de", "it", "zh", "nl", "ja","fr"]

# MRR data for test
mrr_results = {}
samples = {}
for lang in languages:
    fulldf_path = Path(f"/Users/leonardo/git/malco/final_multilingual_output/{lang}/full_df_results.tsv")
    df_onelang = pd.read_csv(fulldf_path, delimiter="\t")
    mrr = df_onelang.groupby("label")["reciprocal_rank"].max()
    std = mrr.std()
    mrr_results[lang] = [mrr.mean(), std, std/math.sqrt(len(df_onelang.groupby("label")))]
    ranks = mrr.apply(lambda x: 1/x if x>0.099 else 11)
    samples[lang] = ranks.tolist()

#print(mrr_results)
# Chi2 is for categorical, not cardinal data! --> use Kruskal Wallis test

kr_correct = kruskal(*samples.values(), axis = 0) 
print("\n\nKruskal-Wallis test result:", kr_correct)
