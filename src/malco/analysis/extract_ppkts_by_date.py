# This script extracts the field .metaData.externalReferences from all json files in a directory and saves them in a dictionary

import json
import os
from metapub import PubMedFetcher 
import datetime
from tqdm import tqdm

# Path to the directory containing the JSON files
ppkts_dir = '/Users/leonardo/data/ppkts_4967_polyglot/jsons'

# Set up the NCBI API key
# Uncomment the following lines to read the API key from a file
"""# read key file ~/ncbi.key
with open(os.path.expanduser('~/ncbi.key'), 'r') as f:
    os.environ['NCBI_API_KEY'] = f.read().strip()
"""

# Iterate over all json files in the directory and populate a dictionary with as a key the filename and as a value the field .metaData.externalReferences
ppkts = {}
for filename in os.listdir(ppkts_dir):
    if filename.endswith('.json'):
        with open(os.path.join(ppkts_dir, filename), 'r') as f:
            data = json.load(f)
            # Check if the key exists in the JSON data
            if 'metaData' in data and 'externalReferences' in data['metaData']:
                ppkts[filename] = data['metaData']['externalReferences']
            else:
                print(f"Key not found in {filename}")

# for each item in the dictionary, take the "id" field and use it to fetch the corresponding PubMed article's date of publication
fetcher = PubMedFetcher()
pubmed_data = {}
for filename, references in tqdm(ppkts.items(), desc="Fetching PubMed data"):
    for reference in references:
        if 'id' in reference: # result has 729 entries, one per pubmed article
            pmid = reference['id']
            # strip the "PMID:" prefix if it exists
            pmid = pmid.replace("PMID:", "").strip()
            try:
                article = fetcher.article_by_pmid(pmid)
                pubmed_data[pmid] = {
                    'date': article.history['entrez']
                }
            except Exception as e:
                print(f"Error fetching data for {pmid}: {e}")

pubmeds_after_cutoff = {}
# Go over pumbed_data which contains a datetime.datetime object and collect those received after October 2023 in pubmeds_after_cutoff
for pmid, data in pubmed_data.items():
    if data['date'] > datetime.datetime(2023, 10, 1):
        pubmeds_after_cutoff[pmid] = data
        print(f"PMID: {pmid}, Date: {data['date']}")

new_ppkts=[]
for fn, _ in ppkts.items():
    for id in pubmeds_after_cutoff.keys():
        if id in fn:
            new_ppkts.append(fn)

output_file = "ppkts_after_oct23.txt"  # Specify the output file name
with open(output_file, "w") as f:
    for item in new_ppkts:
        f.write(item + "\n")  # Write each item followed by a newline character

print(f"Saved {len(new_ppkts)} items to {output_file}")