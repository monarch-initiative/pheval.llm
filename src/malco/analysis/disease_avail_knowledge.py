# Let us try to parametrize how much is known about the diseases, there are two ideas beyond eval_diagnose_category, looking at the MONDO categories
# Idea (0), (number of HPOs present, number of HPOs excluded) correlated to diseases found?
# (1) HPOA and (2) Monarch KG
# (1) Parse out disease genes discovered after 2008/9 (First thing in HPOA)
#     Look for a correlation between date annotated and disease correctly diagnosed. 
#     Hypothesis: the older the easier to diagnose
# (2) To start, looking at the two broad categories found/not-found, count average number of all links
#     After that, count average number of links of some kind
#     Then, something more graphy, such as, centrality? Maybe need to project out something first to find signal in the noise...
import sys
import pandas as pd
import numpy as np
import datetime as dt

hpoa_file_path = "/Users/leonardo/IdeaProjects/maxodiff/data/phenotype.hpoa"
hpoa_df = pd.read_csv(
        hpoa_file_path, sep="\t" , header=4
    )

hpoa_cleaned = pd.DataFrame()
hpoa_cleaned["database_id"] = hpoa_df["database_id"]
hpoa_cleaned['date'] = hpoa_df["biocuration"].str.extract(r'\[(.*?)\]')
#string_dates = str(hpoa_df["biocuration"].str.extract(r'\[(.*?)\]'))
# Mi sto un po attorcigliando, sarebbe da, semplicemente, fare un color coding
#hpoa_cleaned['date'] = [dt.datetime.strptime(day, '%Y-%m-%d').date() for day in string_dates]
hpoa_cleaned = hpoa_cleaned[hpoa_cleaned['database_id'].str.startswith("OMIM")]

model = str(sys.argv[1])
ranking_results_filename = f"out_openAI_models/multimodel/{model}/full_df_results.tsv"
rank_results_df = pd.read_csv(
        ranking_results_filename, sep="\t" 
    )

found_diseases = []
not_found_diseases = []
ppkts = rank_results_df.groupby("label")[["term", "correct_term", "is_correct"]] 
for ppkt in ppkts:
    # is there a true? ppkt is tuple ("filename", dataframe) --> ppkt[1] is a dataframe 
    disease = ppkt[1].iloc[0]['correct_term']
    if any(ppkt[1]["is_correct"]):
       found_diseases.append(disease)
    else:
       not_found_diseases.append(disease)

found_set = set(found_diseases)
notfound_set = set(not_found_diseases)
overlap = []

for i in found_set:
   if i in notfound_set:
      overlap.append(i)

print(f"Number of found diseases by {model} is {len(found_set)}.")
print(f"Number of not found diseases by {model} is {len(notfound_set)}.")
print(f"Found diseases also present in not-found set, by {model} is {len(overlap)}.\n")
# Need some more statistic

# header = ["disease_id", "found", "date"]

# Problematic, goes from 27 k unique values to 8.2k
hpoa_cleaned = hpoa_cleaned.drop_duplicates(subset='database_id')
# Idea here could be to look at the 263-129 (gpt-4o) found diseases not present in not found set and the opposite
# namely never found diseases and look for a correlation with date.
always_found = found_set - notfound_set # 134
never_found = notfound_set - found_set # 213

results_dict = {} # turns out being 281 long 
found_dict = {}
notfound_dict = {}

# TODO
results_df = pd.DataFrame(columns=["disease", "found", "date"])

for af in always_found:
   try:
      results_dict[af] = [True, hpoa_cleaned.loc[hpoa_cleaned['database_id'] == af, 'date'].item() ]
      found_dict[af] = hpoa_cleaned.loc[hpoa_cleaned['database_id'] == af, 'date'].item()
      results_df
   except ValueError:
      print(f"No HPOA for {af}.")
for nf in never_found:
   try:
      results_dict[nf] = [False, hpoa_cleaned.loc[hpoa_cleaned['database_id'] == nf, 'date'].item() ]
      notfound_dict[nf] = hpoa_cleaned.loc[hpoa_cleaned['database_id'] == af, 'date'].item()
   except ValueError:
      print(f"No HPOA for {nf}.")

res_to_clean = pd.DataFrame.from_dict(results_dict).transpose()
res_to_clean.columns=["found","date"]
res_to_clean.date = pd.to_datetime(res_to_clean.date).values.astype(np.int64)
final_avg = pd.DataFrame(pd.to_datetime(res_to_clean.groupby('found').mean().date))
print(final_avg)