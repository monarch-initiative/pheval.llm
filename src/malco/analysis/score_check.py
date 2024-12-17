# check how many correctly counted outputs are not direct matches nor OMIMPS
import pandas as pd
from oaklib import get_adapter
from oaklib.interfaces import OboGraphInterface
from tqdm import tqdm
import os

def mondo_adapter() -> OboGraphInterface:
    """
    Get the adapter for the MONDO ontology.

    Returns:
        Adapter: The adapter.
    """
    return get_adapter("sqlite:obo:mondo")

def omim_mappings(term: str):
    omims = []
    for m in adapter.sssom_mappings([term], source="OMIM"):
        if m.predicate_id == "skos:exactMatch":
            omims.append(m.object_id)
    return omims

model = 'gpt-4o'

out_file = f"/Users/leonardo/git/malco/analysis_out/curategpt_score_errors_{model}.tsv"
#out_file = f"/Users/leonardo/git/malco/analysis_out/score_errors_{model}.tsv"

if not os.path.isfile(out_file):
    results_file_path = f"/Users/leonardo/git/malco/out_multlingual_nov24/multilingual/en/full_df_results.tsv"
    df = pd.read_csv(results_file_path, sep='\t')
    df_matches = df[df["is_correct"]==True][['term','correct_term']]

    adapter = mondo_adapter()

    url = "https://raw.githubusercontent.com/monarch-initiative/mondo/refs/heads/master/src/ontology/mappings/mondo.sssom.tsv"
    url = "/Users/leonardo/.data/oaklib/mondo.sssom.tsv" # for working locally
    # Read the TSV file, skipping lines that start with '#'
    mappings_df = pd.read_csv(url, sep="\t", comment="#")
    tqdm.pandas()

    # Two options, either MONDO maps to PSOMIM, or it maps exactly to correct_term
    def score_func(mondo, omim): # maybe add adapter initialized once only
        ps = mappings_df[(mappings_df['subject_id'] == mondo) &
                        (mappings_df['predicate_id'] == "skos:exactMatch") &
                        (mappings_df['object_id'].str.startswith("OMIMPS"))] [['object_id']]
        mondo_label_df = mappings_df[(mappings_df['subject_id'] == mondo)] [['subject_label']]
        if mondo_label_df.empty==False:
            mondo_label = mondo_label_df.iloc[0]['subject_label']
        else:
            mondo_label = "Unavailable" # possible bug TODO 
        omim_label_df = mappings_df[(mappings_df['object_id'] == omim)] [['object_label']]
        if omim_label_df.empty==False:
            omim_label = omim_label_df.iloc[0]['object_label']
        else:
            mondo_label = "Unavailable"
        # 0 because subject label should always be the same
        if ps.empty==False:
            return ps.iloc[0]["object_id"], mondo_label, omim_label
        else:
            directly_mapped_omims = omim_mappings(mondo)
            if omim in directly_mapped_omims:
                return omim, mondo_label, omim_label
            else:
                return False, mondo_label, omim_label

    df_matches[['match','mondo_label', 'omim_label']] = df_matches.progress_apply(
        lambda row: score_func(row['term'], row['correct_term']), axis=1, result_type='expand')
    #df_matches.to_csv(out_file, sep='\t', index=False)

else:
    df_matches = pd.read_csv(out_file, sep='\t', index_col=False)

df_issues = df_matches[df_matches['match'].astype(str).str.contains('False')]
df_issues.to_csv(out_file, sep='\t', index=False)