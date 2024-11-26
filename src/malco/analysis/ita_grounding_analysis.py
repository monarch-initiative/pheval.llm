from malco.post_process.post_process_results_format import read_raw_result_yaml
from pathlib import Path
import pandas as pd
import os
# Each row has
#    c1      *       c2         *  c3  *       c4         *        c5              *            c6              *  c7                       * c8
# PMID (str) * label/term (str) * rank * ita_reply (bool) * correct_result OMIM ID * correct_result OMIM label  *  MONDO ID (if applicable) * correct? 0/1 (in excel)

# Correct results
file = "/Users/leonardo/git/malco/in_ita_reply/correct_results.tsv"
answers = pd.read_csv(
        file, sep="\t", header=None, names=["description", "term", "label"]
    )

# Mapping each label to its correct term
cres = answers.set_index("label").to_dict() # Cleanup this fella TODO

# Just populate df with two for loops, then sort alfabetically
data = []

# load ita replies
ita_file = Path("/Users/leonardo/git/malco/out_itanoeng/raw_results/multilingual/it/results.yaml")
ita_result = read_raw_result_yaml(ita_file)

# extract input_text from yaml for ita, or extracted_object, terms
for ppkt_out in ita_result:
    extracted_object = ppkt_out.get("extracted_object")
    if extracted_object:
        label = extracted_object.get("label").replace('_it-prompt', '_en-prompt')
        terms = extracted_object.get("terms")
        if terms:
            num_terms = len(terms)
            rank_list = [i + 1 for i in range(num_terms)]
            for term, rank in zip(terms, rank_list):
                data.append({"pubmedid": label, "term": term, "rank": rank, "ita_reply": True, "correct_omim_id": cres[label][0], 
                             "correct_omim_id": cres[label][1], "mondo_id": float('Nan')})


# load eng replies
eng_file = Path("/Users/leonardo/git/malco/out_itanoeng/raw_results/multilingual/it_w_en/results.yaml")
eng_result = read_raw_result_yaml(eng_file)

# extract named_entities, id and label from yaml for eng
# extract input_text from yaml for ita, or extracted_object, terms
for ppkt_out in eng_result:
    extracted_object = ppkt_out.get("extracted_object")
    if extracted_object:
        label = extracted_object.get("label")#.str.replace('_[a-z][a-z]-prompt', '', regex=True)
        terms = extracted_object.get("terms")
        if terms:
            num_terms = len(terms)
            rank_list = [i + 1 for i in range(num_terms)]
            for term, rank in zip(terms, rank_list):
                if term.str.startswith("MONDO"):
                    breakpoint()
                    ne = ppkt_out.get("named_entities")
                    mid = ne.get("id")
                    mlab = ne.get("label") # TODO finish
                else:
                    mlab = float('Nan')

                data.append({"pubmedid": label, "term": term, "rank": rank, "ita_reply": False, "correct_omim_id": cres[label][0], 
                             "correct_omim_id": cres[label][1], "mondo_id": mlab})

# Create DataFrame
column_names = [
    "PMID",
    "diagnosis",
    "rank",
    "ita_reply",
    "correct_OMIMid",
    "correct_OMIMlabel",
    "MONDOid",
]

df = pd.DataFrame(data, columns=column_names)
df = df.sort_values(by = 'Name') 

#df.to_excel(os.getcwd() + "ita_replies2curate.xlsx")
