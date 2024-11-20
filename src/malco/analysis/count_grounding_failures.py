# Quick check how often the grounding failed
# Need to be in short_letter branch
import pandas as pd

mfile = "../outputdir_all_2024_07_04/en/results.tsv"

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
