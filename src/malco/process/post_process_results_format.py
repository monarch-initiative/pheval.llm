import json, yaml, os
from pathlib import Path
from typing import List

import pandas as pd
from oaklib import get_adapter

from malco.process.df_save_util import safe_save_tsv
from malco.process.cleaning import clean_service_answer
from malco.process.grounding import ground_diagnosis_text_to_mondo


def read_raw_result_yaml(raw_result_path: Path) -> List[dict]:
    """
    Read the raw result file.

    Args:
        raw_result_path(Path): Path to the raw result file.

    Returns:
        dict: Contents of the raw result file.
    """
    with open(raw_result_path, "r") as raw_result:
        return list(
            yaml.safe_load_all(raw_result.read().replace("\x04", ""))
        )  # Load and convert to list


def read_result_json(path: str) -> List[dict]:
    """
    Read the raw result file.

    Args:
        path (str): Path to the raw result file.

    Returns:
        List[dict]: Contents of the raw result file.
    """
    responses = []
    with open(path, "r") as raw_result:
        for line in raw_result:
            responses.append(json.loads(line))
    return responses

def create_single_standardised_results(result_file: Path) -> pd.DataFrame:
    data = []
    annotator = get_adapter("sqlite:obo:mondo")
    result = read_result_json(result_file)
        # response = line.get("response")
        # cleaned_text = clean_service_answer(response)

        # assert cleaned_text != "", "Cleaning failed: the cleaned text is empty."
        # grounded = ground_diagnosis_text_to_mondo(
        #     annotator, response, verbose=False, include_list=["MONDO:"]
        # )
        # Migrate grounding responses here like in notebooks
    
    responses = pd.DataFrame({
        "service_answers": result.map(lambda x: x["response"]),
        "metadata": result.map(lambda x: x["id"]),
    })

    responses['service_answer'].progress_apply(
        lambda x: ground_diagnosis_text_to_mondo(annotator, clean_service_answer(x["response"]), verbose=False)
    )


    # Create DataFrame
    df_new = pd.DataFrame(data)
    df = pd.concat([already_computed_df, df_new], axis=0, ignore_index=True)

    # Save DataFrame to TSV
    # output_path = output_dir / output_file_name
    # safe_save_tsv(output_dir, output_file_name, df)

    return df


def create_standardised_results(
    curategpt: bool, results_: Path, output_dir: Path, output_file_name: str
) -> pd.DataFrame:

    data = []
    if curategpt:
        outfile = output_dir / output_file_name
        annotator = get_adapter("sqlite:obo:mondo")
        if os.path.isfile(outfile):
            already_computed_df = pd.read_csv(outfile, sep="\t")
        else:
            already_computed_df = pd.DataFrame()
    for raw_result_path in raw_results_dir.iterdir():
        if raw_result_path.is_file():
            # Cannot have further files in raw_result_path!
            all_results = read_raw_result_yaml(raw_result_path)
            # TODO Change to do use curategpt directly on other file paths
            for this_result in all_results:
                extracted_object = this_result.get("extracted_object")
                if extracted_object:
                    label = extracted_object.get("label")
                    
                    # Adds possibility of continuation runs for curategpt, use with care
                    if curategpt and not already_computed_df.empty:
                        if any(already_computed_df['label'].str.contains(label)):
                            continue
                    terms = extracted_object.get("terms")
                    if curategpt and terms:
                        ontogpt_text = this_result.get("input_text")
                        # its a single string, should be parseable through curategpt
                        cleaned_text = clean_service_answer(ontogpt_text)
                        assert cleaned_text != "", "Cleaning failed: the cleaned text is empty."
                        result = ground_diagnosis_text_to_mondo(
                            annotator, cleaned_text, verbose=False, include_list=["MONDO:"]
                        )
                        # terms will now ONLY contain MONDO IDs OR 'N/A'.
                        # The latter should be dealt with downstream
                        new_terms = []
                        for i in result:
                            if i[1] == [("N/A", "No grounding found")]:
                                new_terms.append(i[0])
                            else:
                                new_terms.append(i[1][0][0])
                        terms = new_terms
                        # terms = [i[1][0][0] for i in result]  # MONDO_ID
                    if terms:
                        # Note, the if allows for rerunning ppkts that failed due to connection issues
                        # We can have multiple identical ppkts/prompts in results.yaml
                        # as long as only one has a terms field
                        num_terms = len(terms)
                        score = [1 / (i + 1) for i in range(num_terms)]  # score is reciprocal rank
                        rank_list = [i + 1 for i in range(num_terms)]
                        for term, scr, rank in zip(terms, score, rank_list):
                            data.append({"label": label, "term": term, "score": scr, "rank": rank})

    # Create DataFrame
    df_new = pd.DataFrame(data)
    df = pd.concat([already_computed_df, df_new], axis=0, ignore_index=True)

    # Save DataFrame to TSV
    # output_path = output_dir / output_file_name
    # safe_save_tsv(output_dir, output_file_name, df)

    return df
