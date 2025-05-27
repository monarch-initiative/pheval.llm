import pandas as pd
from pathlib import Path
import sys

try:
    file = Path(sys.argv[1])
except IndexError:
    print("No input file provided. Using default.")
    # Default file path
    file = Path("final_multilingual_output/rank_data/topn_result.tsv")

df = pd.read_csv(file, delimiter="\t")
language_mapping = {
    "en": "English",
    "es": "Spanish",
    "cs": "Czech",
    "tr": "Turkish",
    "de": "German",
    "it": "Italian",
    "zh": "Chinese",
    "nl": "Dutch",
    "ja": "Japanese",
    "fr": "French",
}

# Replace the short language codes with full names
df["language"] = df["language"].replace(language_mapping)

valid_cases = df["num_cases"]
df["Top-1"] = (df["n1"]) 
df["Top-3"] = (df["n1"] + df["n2"] + df["n3"]) 
df["Top-5"] = (df["n1"] + df["n2"] + df["n3"] + df["n4"] + df["n5"])
df["Top-10"] =  (
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
df["Not Ranked"] = (df["nf"] + df["grounding_failed"]) 
df['No Diagnosis'] = 4917 - df['num_cases']

columns_to_keep = ["language", "Top-1", "Top-3", "Top-10", "Not Ranked", "No Diagnosis"]
df = df[columns_to_keep]
print(df.to_string(index=False))
print(df.to_csv(sep="\t", index=False))