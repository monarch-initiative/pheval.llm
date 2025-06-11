""" This script extracts the field .metaData.externalReferences from all json files in a directory and saves them in a dictionary.
It then uses the PubMedFetcher to fetch the corresponding PubMed article's date of publication for each reference.
The output is a dictionary with the PubMed IDs as keys and their publication dates as values.

Needs an NCBI API key to work. The key can be set in the environment variable NCBI_API_KEY or read from a file.
"""

import json
import os
from metapub import PubMedFetcher 
import datetime
from tqdm import tqdm
import sys
# Check if the script is being run directly


# Path to the directory containing the JSON files as cli input
try:
    ppkts_dir = str(sys.argv[1])
except IndexError:
    ppkts_dir = '/Users/leonardo/data/ppkts_4967_polyglot/jsons'

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Set up the NCBI API key
# Uncomment the following lines to read the API key from a file (does not work...)
"""# Read key file ~/ncbi.key
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

pmid_list = []
# Iterate over the dictionary and make a list on unique PubMed IDs
for filename, references in ppkts.items():
    for reference in references:
        if 'id' in reference:  
            pmid_list.append(reference['id'].replace("PMID:", "").strip())
pmid_list = list(set(pmid_list))  # Remove duplicates
# Print the number of unique PubMed IDs found
print(f"Found {len(pmid_list)} unique PubMed IDs.")

# For each item in the dictionary, take the "id" field and use it to fetch the corresponding PubMed article's date of publication
fetcher = PubMedFetcher()
pmid2date_dict = {}
for pmid in tqdm(pmid_list, desc="Fetching PubMed data", unit="PMID"):
    try:
        article = fetcher.article_by_pmid(pmid)
        pmid2date_dict['PMID:'+pmid] = {
            'date': article.history['entrez']
        }
    except Exception as e:
        print(f"Error fetching data for {pmid}: {e}")


# Save the dictionary to a JSON file
# Construct the output file path relative to the script's directory
output_json_file = os.path.join(script_dir, "../../../leakage_experiment", "pmid2date_dict.json")
# Ensure the output directory exists
output_dir = os.path.dirname(output_json_file)
os.makedirs(output_dir, exist_ok=True)
# Write the dictionary to a JSON file
with open(output_json_file, "w") as f:
    json.dump(pmid2date_dict, f, indent=4, default=str)  # Use default=str to handle datetime objects

print(f"Saved dictionary to {output_json_file}")

