import shutil
import os
import re
import glob

fp = "/Users/leonardo/IdeaProjects/phenopacket2prompt/prompts/"

langs = [
    "en",
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
            #fn = fn[0:-14]  # TODO may be problematic if there are 2 "_" before "{langcode}-"
            # Maybe something along the lines of other script disease_avail_knowledge.py
            # ppkt_label = ppkt[0].replace('_en-prompt.txt','')
            fn = fn.replace('_' + lang +'-prompt.txt','')
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
csset = set(promptfiles["cs"])

intersection = enset & esset & deset & itset & nlset & zhset & trset & csset

print("Common ppkts are: ", len(intersection))

# COPY
dst_dir = "/Users/leonardo/git/malco/in_multlingual_nov24/prompts/"
for id in intersection:
    for lang in langs:
        shutil.copy(fp + lang + "/" + id + '_' + lang +'-prompt.txt', dst_dir + lang) 

#        file = glob.glob(fp + lang + "/" + id + "*")
#        for match in file:
#            shutil.copy(match, dst_dir + lang ) 
