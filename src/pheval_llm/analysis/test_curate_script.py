from pathlib import Path
from typing import List

import yaml
from oaklib import get_adapter

from pheval_llm.post_process.extended_scoring import clean_service_answer, ground_diagnosis_text_to_mondo


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


annotator = get_adapter("sqlite:obo:mondo")
some_yaml_res = Path(
    "/Users/leonardo/git/malco/out_openAI_models/raw_results/multimodel/gpt-4/results.yaml"
)

data = []

if some_yaml_res.is_file():
    all_results = read_raw_result_yaml(some_yaml_res)
    j = 0
    for this_result in all_results:
        extracted_object = this_result.get("extracted_object")
        if extracted_object:  # Necessary because this is how I keep track of multiple runs
            ontogpt_text = this_result.get("input_text")
            # its a single string, should be parseable through curategpt
            cleaned_text = clean_service_answer(ontogpt_text)
            assert cleaned_text != "", "Cleaning failed: the cleaned text is empty."
            result = ground_diagnosis_text_to_mondo(annotator, cleaned_text, verbose=False)

            label = extracted_object.get("label")  # pubmed id
            # terms will now ONLY contain MONDO IDs OR 'N/A'. The latter should be dealt with downstream
            terms = [i[1][0][0] for i in result]
            # terms = extracted_object.get('terms') # list of strings, the mondo id or description
            if terms:
                # Note, the if allows for rerunning ppkts that failed due to connection issues
                # We can have multiple identical ppkts/prompts in results.yaml as long as only one has a terms field
                num_terms = len(terms)
                score = [1 / (i + 1) for i in range(num_terms)]  # score is reciprocal rank
                rank_list = [i + 1 for i in range(num_terms)]
                for term, scr, rank in zip(terms, score, rank_list):
                    data.append({"label": label, "term": term, "score": scr, "rank": rank})
        if j > 20:
            break
        j += 1
