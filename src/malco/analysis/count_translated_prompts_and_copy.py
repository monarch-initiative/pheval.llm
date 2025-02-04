"""Look in the phenopacket2prompt output directory for the common phenopackets across languages and copy them to an input directory."""

import os
import re
import shutil

fp = "/Users/leonardo/IdeaProjects/phenopacket2prompt/prompts/"

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

intersection = enset & esset & deset & itset  & zhset & trset & csset & jaset  & nlset

print("Common ppkts are: ", len(intersection))


# COPY
dst_dir = "/Users/leonardo/git/malco/in_multlingual22jan_gpt4/prompts/"
for id in intersection:
    for lang in langs:
        shutil.copy(fp + lang + "/" + id + "_" + lang + "-prompt.txt", dst_dir + lang)
