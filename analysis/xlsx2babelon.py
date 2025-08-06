"""
Create babelon complying tables from .xlsx that was sent to us
"""

import pandas as pd

tr_lang_code = "tr"

tr_lang = "turkish-1"
data_path = "/Users/leonardo/data/translate_missing/"
data_file = data_path + "missing_hp_" + tr_lang + ".xlsx"


babelon_names = [
    "source_language",
    "source_value",
    "subject_id",
    "predicate_id",
    "translation_language",
    "translation_value",
    "translation_status",
    "translator",
    "translator_expertise",
    "translation_date",
]


df = pd.DataFrame(columns=babelon_names)
df[["source_value", "translation_value"]] = pd.read_excel(data_file, header=None, usecols="A:B")
df[["source_value", "subject_id"]] = df["source_value"].str.split("(", n=1, expand=True)
df["subject_id"] = df["subject_id"].str.replace(")", "")
df["translation_value"] = df["translation_value"].str.replace(r"\(.*\)", "", regex=True)
df["source_language"] = "en"
df["predicate_id"] = "rdfs:label"
df["translation_language"] = tr_lang_code
df["translation_status"] = "CANDIDATE"
df["translator"] = "DeepL"
df["translator_expertise"] = "ALGORITHM"
df["translation_date"] = "2024-09-11"

df.to_excel(data_path + "hp-" + tr_lang_code + "-babelon.xlsx", index=False)
