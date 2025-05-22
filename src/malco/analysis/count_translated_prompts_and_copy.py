"""Look in the phenopacket2prompt output directory for the common phenopackets across languages and copy them to an input directory."""

import os
import re
import shutil
import tqdm

fp = "/Users/leonardo/IdeaProjects/phenopacket2prompt/6668prompts/"

langs = [
    "en",
    "ja",
    "es",
    "de",
    "it",
    "nl",
    "tr",
    "zh",
    "cs",
    "fr",
]

promptfiles = {}
for lang in langs:
    promptfiles[lang] = []
    for dirpath, dirnames, filenames in os.walk(fp + lang):
        for fn in filenames:
            fn = fn.replace("_" + lang + "-prompt.txt", "")
            promptfiles[lang].append(fn)
        break

intersection = set()

enset = set(promptfiles["en"])
esset = set(promptfiles["es"])
deset = set(promptfiles["de"])
itset = set(promptfiles["it"])
nlset = set(promptfiles["nl"])
zhset = set(promptfiles["zh"])
trset = set(promptfiles["tr"])
jaset = set(promptfiles["ja"])
csset = set(promptfiles["cs"])
frset = set(promptfiles["fr"])

intersection = enset & esset & deset & itset  & zhset & trset & csset & jaset  & nlset & frset

print("Common ppkts are: ", len(intersection))

output_file = "final_multilingual_output/ppkts_4917set.txt"  # Specify the output file name
with open(output_file, "w") as f:
    for item in intersection:
        f.write(item + "_en-prompt.txt\n")  # Write each item followed by a newline character

"""# COPY
dst_dir = "/Users/leonardo/git/malco/in_multlingual_nov24/prompts/"
for id in tqdm.tqdm(intersection, "Copying files..."):
    for lang in langs:
        shutil.copy(fp + lang + "/" + id + "_" + lang + "-prompt.txt", dst_dir + lang)"""
