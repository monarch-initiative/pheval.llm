from pathlib import Path
from typing import List

import yaml
import json
import os, shutil

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

def safe_save_tsv(path, filename, df):
    full_path = path / filename
    # If full_path already exists, prepend "old_"
    # It's the user's responsibility to know only up to 2 versions can exist, then data is lost
    if os.path.isfile(full_path):
        old_full_path = path / ("old_" + filename)
        if os.path.isfile(old_full_path):
            os.remove(old_full_path)
        shutil.copy(full_path, old_full_path)
        os.remove(full_path)
    df.to_csv(full_path, sep="\t", index=False)