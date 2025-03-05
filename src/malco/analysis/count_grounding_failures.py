""" Quick check how often the grounding failed
Need to be in short_letter branch"""
import pandas as pd
from pathlib import Path

# Multi-lingual results
languages = ["en", "es", "cs", "tr", "de", "it", "zh", "nl", "ja"]

for lang in languages:
    fulldf_path = Path(f"/Users/leonardo/git/malco/out_multlingual_nov24/multilingual/{lang}/full_df_results.tsv")
    df_onelang = pd.read_csv(fulldf_path, delimiter="\t")
    found_n_not = df_onelang['term'].str.startswith("MONDO").value_counts()
    
    print(lang, f"grounding failures {found_n_not.iloc[1]} of {found_n_not.iloc[0]}, {100*found_n_not.iloc[1]/df_onelang.shape[0]}%")


# Short letter results
mfile = "outputdir_all_2024_07_04/en/results.tsv"
df = pd.read_csv(mfile, sep="\t")  # , header=None, names=["description", "term", "label"]

terms = df["term"]
counter = 0
grounded = 0
for term in terms:
    if term.startswith("MONDO"):
        grounded += 1
    else:
        counter += 1

print(counter)
print(grounded)
