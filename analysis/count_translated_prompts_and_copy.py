"""Look in the phenopacket2prompt output directory for the common phenopackets across languages and copy them to another directory.
"""

import os
import re
import shutil
import tqdm
import sys
import json


create_list_file = False
copy_prompt_files = False
copy_json_files = True

try:
    fp = sys.argv[1]
except IndexError:
    print("No path provided, using default path.")
    # Default path to the phenopacket2prompt output directory
    fp = "/Users/leonardo/IdeaProjects/phenopacket2prompt/6668prompts/"

try:
    output_file = sys.argv[2]
except IndexError:
    print("No output file provided, using default output file.")
    # Default output file to save the common phenopackets
    output_file = "final_multilingual_output/ppkts_4917set.txt"  # Specify the output file name

try:
    dst_dir = sys.argv[3]
except IndexError:
    # Default destination directory to copy the files
    print("No destination directory provided, using default destination directory.")
    dst_dir = "/Users/leonardo/data/4917_poly_ppkts"

# Take as a second argument the list of languages to consider
if len(sys.argv) > 4:
    langs = sys.argv[4].split(",")
else:
    # Default languages to consider
    langs = ["en", "ja", "es", "de", "it", "nl", "tr", "zh", "cs", "fr"]
    print("No languages provided, using default languages: ", langs, "\nYou can provide them as a comma-separated list as the second argument.")

promptfiles = {}
for lang in langs:
    promptfiles[lang] = []
    for dirpath, dirnames, filenames in os.walk(fp + lang):
        for fn in filenames:
            fn = fn.replace("_" + lang + "-prompt.txt", "")
            promptfiles[lang].append(fn)
        break

intersection = set()

# Convert lists to sets for intersection
promptfiles = {lang: set(files) for lang, files in promptfiles.items()}

# Create an intersection set of all languages
# Initialize the intersection with the first language's set
if langs:
    intersection = promptfiles[langs[0]]
# Intersect with the sets of the other languages
for lang in langs[1:]:
    intersection &= promptfiles[lang]

print("Common ppkts are: ", len(intersection))

if create_list_file:
    with open(output_file, "w") as f:
        for item in intersection:
            f.write(item + "_en-prompt.txt\n")  # Write each item followed by a newline character

# Copy prompts
if copy_prompt_files:
    for id in tqdm.tqdm(intersection, "Copying files..."):
        for lang in langs:
            shutil.copy(fp + lang + "/" + id + "_" + lang + "-prompt.txt", dst_dir + lang)

# Copy jsons
if copy_json_files:
    json_path = os.path.join(fp, "original_phenopackets")
    for jsonfile in tqdm.tqdm(os.listdir(json_path), "Copying json files..."):
        with open(os.path.join(json_path, jsonfile), 'r') as f:
            data = json.load(f)
            id = data['id']
            id = re.sub(r'[^\w]', '_', id)
            if id in intersection:
                shutil.copy(os.path.join(json_path, jsonfile), os.path.join(dst_dir, "jsons", jsonfile))
            else:
                print(f"Skipping {jsonfile}, not in intersection.")
