import os
import re
fp = "/Users/leonardo/IdeaProjects/phenopacket2prompt/prompts/"

langs = ["en",
         "es",
         "de",
         "it",
         "nl",
         "tr",
         "zh",
         ]

promptfiles = {}
for lang in langs:
    promptfiles[lang] = []
    for (dirpath, dirnames, filenames) in os.walk(fp + lang):
        for fn in filenames:
            fn = fn[0:-14]  # TODO may be problematic if there are 2 "_" before "{langcode}-"
            # Maybe something along the lines of other script disease_avail_knowledge.py
            # ppkt_label = ppkt[0].replace('_en-prompt.txt','')
            promptfiles[lang].append(fn)
        break

intersection = set()

enset = set(promptfiles['en'])
esset = set(promptfiles['es'])
deset = set(promptfiles['de'])
itset = set(promptfiles['it'])
nlset = set(promptfiles['nl'])
zhset = set(promptfiles['zh'])
trset = set(promptfiles['tr'])

intersection = enset & esset & deset & itset & nlset & zhset & trset

print("Common ppkts are: ", len(intersection))
