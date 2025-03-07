import json, yaml, os
from pathlib import Path
from typing import List
import pandas as pd
from oaklib import get_adapter
from malco.process.cleaning import split_diagnosis_from_header
from malco.process.grounding import ground_diagnosis_text_to_mondo
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

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

def create_single_standardised_results(responses: pd.DataFrame) -> pd.DataFrame:
    with ThreadPoolExecutor() as executor:
        results = list(tqdm(executor.map(_process_row, [row for _, row in responses.iterrows()]), total=len(responses)))
    responses['grounding'] = results

    # Save DataFrame to TSV
    # output_path = output_dir / output_file_name
    # safe_save_tsv(output_dir, output_file_name, df)
    return responses

def _process_row(row):
      annotator = get_adapter("sqlite:obo:mondo")
      return ground_diagnosis_text_to_mondo(annotator, split_diagnosis_from_header(row["service_answers"]), verbose=False)