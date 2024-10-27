"""This script looks for correlations between the ability of an LLM to 
diagnose the correct disease and certain parameters.

(1) The first idea is using time, namely dates of discovery, as a way to capture how much of a 
disease is present in the web. This is a proxy for how much an LLM knows about such a diseases.
We use HPOA, we do not parse out disease genes discovered after 2008 though (first thing in HPOA)

(2) Then we could look at some IC(prompt) as a second proxy. To start, avg(IC) as computed with

`runoak -g hpoa_file -G hpoa -i hpo_file  information-content -p i --use-associations .all`

Finally, if the two things correlate, can we use them to train a logit or SVM to predict whether
the LLM will be successfull or not?
"""
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
import sys
import os
import pandas as pd
import numpy as np
import datetime as dt
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import json
import re
import pickle

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Parse input:
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
model = str(sys.argv[1])
try:
   make_plots = str(sys.argv[2])=="plot"
except IndexError:
   make_plots = False
   print("\nYou can pass \"plot\" as a second CLI argument and this will generate nice plots!\n")
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# PATHS:
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
data_dir = Path.home() / "data"
hpoa_file_path = data_dir / "phenotype.hpoa"
ic_file = data_dir / "ic_hpoa.txt"
original_ppkt_dir = data_dir / "ppkt-store-0.1.19"
outdir =  Path.cwd() / "src" / "malco" / "analysis" / "time_ic"
ranking_results_filename = f"out_openAI_models/multimodel/{model}/full_df_results.tsv"

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# IMPORT
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
with open(outdir / "rank_date_dict.pkl", 'rb') as f:
    rank_date_dict = pickle.load(f)
# import df of LLM results
rank_results_df = pd.read_csv(
        ranking_results_filename, sep="\t" 
    )

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ANALYSIS STARTS HERE:
# Look for correlation in box plot of ppkts' rank vs time
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
dates = []
dates_wo_none = [] # messy workaround
ranks = []
ranks_wo_none = []
for key, data in rank_date_dict.items():
   r = data[0]
   d = dt.datetime.strptime(data[1], '%Y-%m-%d').date()
   dates.append(d)
   ranks.append(r)
   if r is not None:
      dates_wo_none.append(d)
      ranks_wo_none.append(r)
   
   
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Correlation? 
years_only = []
for i in range(len(dates)): 
   years_only.append(dates[i].year)

years_only_wo_none = []
for i in range(len(dates_wo_none)): 
   years_only_wo_none.append(dates[i].year)

if make_plots:
   sns.boxplot(x=years_only_wo_none, y=ranks_wo_none)
   plt.xlabel("Year of HPOA annotation")
   plt.ylabel("Rank")
   plt.title("LLM performance uncorrelated with date of discovery")
   #TODO change show to save
   plt.show()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Statistical test, simplest idea: chi2 of contingency table with:
# y<=2009 and y>2009 clmns and found vs not-found counts, one count per ppkt
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
cont_table = [[0, 0], [0, 0]] # contains counts

for i, d in enumerate(years_only):
   if d < 2010:
      if ranks[i] == None:
         cont_table[0][1] += 1
      else:
         cont_table[0][0] += 1
   else:
      if ranks[i] == None:
         cont_table[1][1] += 1
      else:
         cont_table[1][0] += 1

df_contingency_table = pd.DataFrame(cont_table, 
                                    index=["found", "not_found"], 
                                    columns=["y<2010", "y>=2010"])
print(df_contingency_table)
print("H0: no correlation between column 1 and 2:")
from scipy.stats import chi2_contingency
res = chi2_contingency(cont_table) 
print("Results from \u03c7\N{SUPERSCRIPT TWO} test on contingency table:\n", res)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# IC: For each phenpacket, list observed HPOs and compute average IC. Is it correlated with 
# success? I.e., start with f/nf, 1/0 on y-axis vs avg(IC) on x-axis

# Import ppkts
ppkts = rank_results_df.groupby("label")[["term", "correct_term", "is_correct", "rank"]] 

# Import IC-file as dict
with open(ic_file) as f:
    ic_dict = dict(i.rstrip().split(None, 1) for i in f)

ppkt_ic = {}
missing_in_ic_dict = []
ppkts_with_zero_hpos = []

ppkts_with_missing_hpos = []
# Iterate over ppkts, which are json. 
for subdir, dirs, files in os.walk(original_ppkt_dir):
   # For each ppkt
   for filename in files:
      if filename.endswith('.json'):
         file_path = os.path.join(subdir, filename)
         with open(file_path, mode="r", encoding="utf-8") as read_file:
            ppkt = json.load(read_file)
         ppkt_id = re.sub('[^\\w]', '_', ppkt['id'])
         ic = 0 
         num_hpos = 0
         # For each HPO
         for i in ppkt['phenotypicFeatures']:
            try:
               if i["excluded"]: # skip excluded
                  continue
            except KeyError:
               pass
            hpo = i["type"]["id"]
            try:
               ic += float(ic_dict[hpo])
               num_hpos += 1
            except KeyError as e:
               missing_in_ic_dict.append(e.args[0])
               ppkts_with_missing_hpos.append(ppkt_id)

               #print(f"No entry for {e}.")
            
         # For now we are fine with average IC
         try:
            ppkt_ic[ppkt_id] = ic/num_hpos
            # TODO max ic instead try
         except ZeroDivisionError as e: 
            ppkts_with_zero_hpos.append(ppkt_id)
            #print(f"No HPOs for {ppkt["id"]}.")
  
missing_in_ic_dict_unique = set(missing_in_ic_dict)
ppkts_with_missing_hpos = set(ppkts_with_missing_hpos)
print(f"\nNumber of (unique) HPOs without IC-value is {len(missing_in_ic_dict_unique)}.") # 65
print(f"Number of ppkts with zero observed HPOs is {len(ppkts_with_zero_hpos)}. These are left out.") # 141
#TODO check 141 
print(f"Number of ppkts where at least one HPO is missing its IC value is {len(ppkts_with_missing_hpos)}. These are left out from the average.\n") # 172

ppkt_ic_df = pd.DataFrame.from_dict(ppkt_ic, orient='index', columns=['avg(IC)'])
ppkt_ic_df['Diagnosed'] = 0  

for ppkt in ppkts:
   if any(ppkt[1]["is_correct"]):
      ppkt_label = ppkt[0].replace('_en-prompt.txt','')
      if ppkt_label in ppkts_with_zero_hpos:
         continue
      ppkt_ic_df.loc[ppkt_label,'Diagnosed'] = 1 

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# See https://github.com/monarch-initiative/phenopacket-store/issues/157
label_manual_removal = ["PMID_27764983_Family_1_individual__J", 
                        "PMID_35991565_Family_I__3"]
ppkt_ic_df = ppkt_ic_df.drop(label_manual_removal)
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# ppkt_ic_df['Diagnosed'].value_counts()
# Diagnosed
# 0.0    4182   64%
# 1.0    2347   36%
ppkt_ic_df.to_csv(outdir / "ppkt_ic.tsv", sep='\t', index=True)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# T-test: unlikely that the two samples are such due to sample bias.
# Likely, there is a correlation between average IC and whether the case is being solved.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# One-sample Kolmogorov-Smirnov test: compares the underlying distribution F(x) of a sample 
# against a given distribution G(x), here the normal distribution
from scipy.stats import kstest
kolsmirnov_result = kstest(ppkt_ic_df['avg(IC)'],'norm')
print(kolsmirnov_result,"\n")
# When interpreting be careful, and I quote one answer from: 
# https://stats.stackexchange.com/questions/2492/is-normality-testing-essentially-useless
# "The question normality tests answer: Is there convincing 
# evidence of any deviation from the Gaussian ideal? 
# With moderately large real data sets, the answer is almost always yes." 

# TODO: regardless of above, our distributions are not normal. Discard t and add non-parametric U-test (Mann-Whitney)
from scipy.stats import ttest_ind
found_ic = list(ppkt_ic_df.loc[ppkt_ic_df['Diagnosed']>0, 'avg(IC)'])
not_found_ic = list(ppkt_ic_df.loc[ppkt_ic_df['Diagnosed']<1, 'avg(IC)'])
tresult = ttest_ind(found_ic, not_found_ic, equal_var=False)
fsum = [np.mean(found_ic),
        np.std(found_ic),
        np.mean(not_found_ic),
        np.std(not_found_ic),
      ] 
if make_plots:
   plt.hist(found_ic, bins=25, color='c', edgecolor='k', alpha=0.5, density=True)
   plt.hist(not_found_ic, bins=25, color='r', edgecolor='k', alpha=0.5, density=True)
   plt.xlabel("Average Information Content")
   plt.ylabel("Counts")
   plt.legend(['Successful Diagnosis', 'Unsuccessful Diagnosis'])
   #TODO change show to save
   plt.show()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# TODO U test for ranks (separate table):
# 1) cont table 8 cells... chi2 test
# 2) MRR test --> one way
# 3) rank based u-test, max 50, 51 for not found or >50


