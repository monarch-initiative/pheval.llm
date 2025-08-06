import pandas as pd

path = "/Users/leonardo/git/malco/data/results/multilingual_main/topn_result_"
suffix = "Meditron3_70B.tsv"
langs = ["", "cs-", "de-", "es-", "fr-", "it-", "ja-", "tr-", "zh-", "nl-"]

df = pd.DataFrame()

for lang in langs:
    df_one_lang = pd.read_csv(
        f"{path}{lang}{suffix}",
        sep="\t",
        usecols=["run", "items_processed", "total_grounding_failures"],
    )
    # Concatenate the dataframes for each language
    df = pd.concat([df, df_one_lang], ignore_index=True)

# Add column percentage which is items_processed / total_grounding_failures
df["percentage"] = df["total_grounding_failures"] / df["items_processed"] * 100

print(df.to_csv(sep="\t", index=False))
