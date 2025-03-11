import os
from pathlib import Path

import pandas as pd

from malco.process.process import read_raw_result_yaml

# Each row has
#    c1      *       c2         *  c3   *       c4         *        c5              *            c6              *  c7                       * c8
# PMID (str) * label/term (str) *       *   rank           * ita_reply (bool) * correct_result OMIM ID * correct_result OMIM label  *  MONDO label (if applicable) * correct? 0/1 (in excel)

# Correct results
file = "/Users/leonardo/git/malco/in_ita_reply/correct_results.tsv"
answers = pd.read_csv(file, sep="\t", header=None, names=["description", "term", "label"])

# Mapping each label to its correct term
cres = answers.set_index("label").to_dict()

# Just populate df with two for loops, then sort alfabetically
data = []

# load ita replies
ita_file = Path("/Users/leonardo/git/malco/out_itanoeng/raw_results/multilingual/it/results.yaml")
ita_result = read_raw_result_yaml(ita_file)

# extract input_text from yaml for ita, or extracted_object, terms
for ppkt_out in ita_result:
    extracted_object = ppkt_out.get("extracted_object")
    if extracted_object:
        label = extracted_object.get("label").replace("_it-prompt", "_en-prompt")
        terms = extracted_object.get("terms")
        if terms:
            num_terms = len(terms)
            rank_list = [i + 1 for i in range(num_terms)]
            for term, rank in zip(terms, rank_list):
                data.append(
                    {
                        "pubmedid": label,
                        "term": term,
                        "mondo_label": float("Nan"),
                        "rank": rank,
                        "ita_reply": True,
                        "correct_omim_id": cres["term"][label],
                        "correct_omim_description": cres["description"][label],
                    }
                )


# load eng replies
eng_file = Path(
    "/Users/leonardo/git/malco/out_itanoeng/raw_results/multilingual/it_w_en/results.yaml"
)
eng_result = read_raw_result_yaml(eng_file)

# extract named_entities, id and label from yaml for eng
# extract input_text from yaml for ita, or extracted_object, terms
for ppkt_out in eng_result:
    extracted_object = ppkt_out.get("extracted_object")
    if extracted_object:
        label = extracted_object.get("label").replace("_it-prompt", "_en-prompt")
        terms = extracted_object.get("terms")
        if terms:
            num_terms = len(terms)
            rank_list = [i + 1 for i in range(num_terms)]
            for term, rank in zip(terms, rank_list):
                if term.startswith("MONDO"):
                    ne = ppkt_out.get("named_entities")
                    for entity in ne:
                        if entity.get("id") == term:
                            mlab = entity.get("label")
                else:
                    mlab = float("Nan")

                data.append(
                    {
                        "pubmedid": label,
                        "term": mlab,
                        "mondo_label": term,
                        "rank": rank,
                        "ita_reply": False,
                        "correct_omim_id": cres["term"][label],
                        "correct_omim_description": cres["description"][label],
                    }
                )

# Create DataFrame
column_names = [
    "PMID",
    "GPT Diagnosis",
    "MONDO ID",
    "rank",
    "ita_reply",
    "correct_OMIMid",
    "correct_OMIMlabel",
]

df = pd.DataFrame(data)
df.columns = column_names
df.sort_values(by=["PMID", "ita_reply", "rank"], inplace=True)
# df.to_excel(os.getcwd() + "ita_replies2curate.xlsx") # does not work, wrong path, not important
