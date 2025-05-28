from pathlib import Path
import re
import pandas as pd
import numpy as np
import sys

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Parse input:
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
try:
    fp = Path(str(sys.argv[1]))
except IndexError:
    fp = Path("/Users/leonardo/IdeaProjects/phenopacket2prompt/narrative_exp_list.txt")
    print('\nYou can pass a txt file with a set of pubmed IDs as a first CLI argument!\n')
try:
    prompt_dir = Path(str(sys.argv[2]))
except IndexError:
    prompt_dir = Path("/Users/leonardo/IdeaProjects/phenopacket2prompt/6687ppkt_prompts/en")
    print('\nYou can pass a directory with the prompts created with phenopacket2prompt as a second CLI argument!\n')
try:
    prompts4malco_dir = Path(str(sys.argv[3]))
except IndexError:
    prompts4malco_dir = Path("/Users/leonardo/git/malco/narrative_input/prompts/")
    print('\nYou can pass a directory to copy the prompts to as a third CLI argument!\n')
try:
    narr_prompts_dir = Path(str(sys.argv[4]))
except IndexError:
    narr_prompts_dir = Path("/Users/leonardo/IdeaProjects/phenopacket2prompt/text_mined/original")
    print('\nYou can pass a directory with the original narrative prompts as a fourth CLI argument!\n')

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


with open(fp, "r") as f:
    case_pid = f.readlines()

case_pid = [x.strip() for x in case_pid]
case_pid = [re.sub(r'.txt', '', x)  for x in case_pid]

# For each case_pid, see if there is a corresponding file starting with that name in the prompt_dir

matches = []
misses = []
multiple = []

# Iterate through each string in case_pid
for pid in case_pid:
    # Find all files in prompt_dir that start with the current pid
    matching_files = [file for file in prompt_dir.iterdir() if file.name.startswith(pid)]
    
    # Categorize based on the number of matches
    if len(matching_files) == 0:
        misses.append(pid)
    elif len(matching_files) == 1:
        matches.append(pid)
    else:
        multiple.append(pid)

# Print or use the results as needed
print(f"There are {len(matches)} matches.")
print(f"There are {len(misses)} misses.")
print(f"There are {len(multiple)} multiple hits.")

#++++++++++++++++++++++++++++++++++++++
# Manual correction of the multiple hits
# Define a dictionary of manual corrections
manual_corrections = {
    "PMID_15673476": "PMID_15673476_proband",
    "PMID_16962354":"PMID_16962354_first_mutation", # because it's a male
#    "PMID_17661815":"", # two patients
    "PMID_20089953":"PMID_20089953_Patient_III_4", 
    "PMID_20932317":"PMID_20932317_SMS324",
#    "PMID_22560515":"", # two patients
#    "PMID_24403049":"", # Two brothers
    "PMID_27180139":"PMID_27180139_case_1",
#    "PMID_27587992":"", # one description for two siblings
    "PMID_28327087":"PMID_28327087_Patient_II_1",
    "PMID_28392951":"PMID_28392951_Patient_1",
#    "PMID_28446873":"", # both _Case1 and _Case2 are present
    "PMID_28757203":"PMID_28757203_Individual_1_P1",
    "PMID_29037160":"PMID_29037160_Case_3_family_III",
    "PMID_29127725":"PMID_29127725_Patient_1",
    "PMID_30053862":"PMID_30053862_Case_II_1",
    "PMID_30642278": "PMID_30642278_individual_II_5",
    "PMID_30643655": "PMID_30643655_F2_IV_1"
}

#++++++++++++++++++++++++++++++++++++++

print("\nUsing matches only...\n")

# For each match, copy the file starting with that name in prompt_dir to prompts4malco_dir+"/std_en" and the file starting with that name in 
# narr_prompts_dir to prompts4malco_dir+"/narrative_en"
for pid in matches:
    # Find the file in prompt_dir
    matching_file = [file for file in prompt_dir.iterdir() if file.name.startswith(pid)][0]
    # Copy it to prompts4malco_dir/"std_en"
    with open(prompts4malco_dir / "std_en" / matching_file.name, 'w') as f:
        f.write(matching_file.read_text())
    print(f"Copied {matching_file.name} to {prompts4malco_dir / 'std_en' / matching_file.name}")
    
    # Find the file in narr_prompts_dir
    matching_file = [file for file in narr_prompts_dir.iterdir() if file.name.startswith(pid)][0]
    # Copy it to prompts4malco_dir/"narrative_en"
    with open(prompts4malco_dir / "narrative_en" / matching_file.name, 'w') as f:
        f.write(matching_file.read_text())
    # Print the name of the copied file
    print(f"Copied {matching_file.name} to {prompts4malco_dir / 'narrative_en' / matching_file.name}")
    # Print the name of the copied file

for item in manual_corrections.keys():
    matching_file = [file for file in prompt_dir.iterdir() if file.name.startswith(manual_corrections[item])][0]
    with open(prompts4malco_dir / "std_en" / matching_file.name, 'w') as f:
            f.write(matching_file.read_text())
    print(f"Copied {matching_file.name} to {prompts4malco_dir / 'std_en' / matching_file.name}")

for item in manual_corrections.keys():
    matching_file = [file for file in narr_prompts_dir.iterdir() if file.name.startswith(item)][0]
    with open(prompts4malco_dir / "narrative_en" / matching_file.name, 'w') as f:
            f.write(matching_file.read_text())
    print(f"Copied {matching_file.name} to {prompts4malco_dir / 'narrative_en' / matching_file.name}")
