"""Compute the unique number of diseases in the multilingual dataset"""

import pandas as pd

langs = ["en",
    "ja",
    "es",
    "de",
    "it",
    "nl",
    "tr",
    "zh",
    "cs",
]

all_mondos = []
for lang in langs:
# import df
    df = pd.read_csv(f"/Users/leonardo/git/malco/out_multlingual_nov24/multilingual/{lang}/full_df_results.tsv", sep='\t')
    all_mondos.extend(df['term'].to_list())

# put all its MONDO terms in set
print("List of diseases is long: ", len(all_mondos))
print("But the unique number is: ", len(set(all_mondos)))
