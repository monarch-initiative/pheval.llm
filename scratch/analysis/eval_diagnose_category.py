import sys

import numpy as np
import pandas as pd
from cachetools import LRUCache, cached
from cachetools.keys import hashkey
from oaklib import get_adapter
from oaklib.datamodels.vocabulary import IS_A, PART_OF
from oaklib.interfaces import MappingProviderInterface, OboGraphInterface
from oaklib.interfaces.obograph_interface import GraphTraversalMethod
from shelved_cache import PersistentCache

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

outpath = "disease_groups/"

pc_cache_file = outpath + "diagnoses_hereditary_cond"
pc = PersistentCache(LRUCache, pc_cache_file, maxsize=4096)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def mondo_adapter() -> OboGraphInterface:
    """
    Get the adapter for the MONDO ontology.

    Returns:
        Adapter: The adapter.
    """
    return get_adapter("sqlite:obo:mondo")


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def mondo_mapping(term, adapter):
    mondos = []
    for m in adapter.sssom_mappings([term], source="OMIM"):
        if m.predicate_id == "skos:exactMatch":
            mondos.append(m.subject_id)
    return mondos


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@cached(pc, key=lambda omim_term, disease_categories, mondo: hashkey(omim_term))
def find_category(omim_term, disease_categories, mondo):
    if not isinstance(mondo, MappingProviderInterface):
        raise ValueError("Adapter is not a MappingProviderInterface")
    # Find ancestors
    mondo_term = mondo_mapping(omim_term, mondo)
    if not mondo_term:
        print(omim_term)
        return None

    ancestor_list = mondo.ancestors(
        mondo_term,  # only IS_A->same result
        # , reflexive=True) # method=GraphTraversalMethod.ENTAILMENT
        predicates=[IS_A, PART_OF],
    )

    for mondo_ancestor in ancestor_list:
        if mondo_ancestor in disease_categories:
            # TODO IMPORTANT! Like this, at the first match the function exits!!
            return mondo_ancestor  # This should be smt like MONDO:0045024 (cancer or benign tumor)

    print("Special issue following:  ")
    print(omim_term)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# =====================================================
# Script starts here. Name model:
model = str(sys.argv[1])
# =====================================================
# Find 42 diseases categories

mondo = mondo_adapter()

disease_categories = mondo.relationships(
    objects=["MONDO:0003847"], predicates=[IS_A, PART_OF]  # hereditary diseases
)  # only IS_A->same result
# disease_categories = mondo.relationships(objects = ["MONDO:0700096"], # only IS_A->same result
#                                         predicates=[IS_A, PART_OF])

# make df contingency table with header=diseases_category, correct, incorrect and initialize all to 0.
header = ["label", "correct", "incorrect"]
dc_list = [i[0] for i in list(disease_categories)]
contingency_table = pd.DataFrame(0, index=dc_list, columns=header)
for j in dc_list:
    contingency_table.loc[j, "label"] = mondo.label(j)
breakpoint()
filename = f"out_openAI_models/multimodel/{model}/full_df_results.tsv"
# label   term    score   rank    correct_term    is_correct      reciprocal_rank
# PMID_35962790_Family_B_Individual_3__II_6__en-prompt.txt        MONDO:0008675   1.0     1.0     OMIM:620545     False        0.0

df = pd.read_csv(filename, sep="\t")

ppkts = df.groupby("label")[["term", "correct_term", "is_correct"]]
count_fails = 0

omim_wo_match = {}
for ppkt in ppkts:
    # find this phenopackets category <cat> from OMIM
    category_index = find_category(ppkt[1].iloc[0]["correct_term"], dc_list, mondo)
    if not category_index:
        count_fails += 1
        # print(f"Category index for {ppkt[1].iloc[0]["correct_term"]} ")
        omim_wo_match[ppkt[0]] = ppkt[1].iloc[0]["correct_term"]
        continue
    # cat_ind = find_cat_index(category)
    # is there a true? ppkt is tuple ("filename"/"label"/what has been used for grouping, dataframe) --> ppkt[1] is a dataframe
    if not any(ppkt[1]["is_correct"]):
        # no  --> increase <cat> incorrect
        try:
            contingency_table.loc[category_index, "incorrect"] += 1
        except:
            print("issue here")
            continue
    else:
        # yes --> increase <cat> correct
        try:
            contingency_table.loc[category_index, "correct"] += 1
        except:
            print("issue here")
            continue

print("\n\n", "===" * 15, "\n")
print(
    f"For whatever reason find_category() returned None in {count_fails} cases, wich follow:\n"
)  # print to file!
# print(contingency_table)
print("\n\nOf which the following are unique OMIMs:\n", set(list(omim_wo_match.values())))
# print(omim_wo_match, "\n\nOf which the following are unique OMIMs:\n", set(list(omim_wo_match.values())))

cont_table_file = f"{outpath}{model}.tsv"
# Will overwrite
# contingency_table.to_csv(cont_table_file, sep='\t')
