import pandas as pd
from oaklib import get_adapter
from tqdm import tqdm

from malco.process.cleaning import split_diagnosis_from_header
from malco.process.grounding import ground_diagnosis_text_to_mondo


def create_single_standardised_results(responses: pd.DataFrame, process) -> pd.DataFrame:
    results = []
    for _, row in tqdm(
        responses.iterrows(),
        total=responses.shape[0],
        position=process,
        desc=f"Grounding Process {process}",
    ):
        annotator = get_adapter("sqlite:obo:mondo")
        results.append(
            ground_diagnosis_text_to_mondo(
                annotator, split_diagnosis_from_header(row["service_answers"]), verbose=False
            )
        )
    responses["grounding"] = results
    return responses
