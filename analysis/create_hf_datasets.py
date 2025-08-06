"""
Create Hugging Face datasets from multilingual prompt files.

This script reads prompt files for multiple languages, associates them with correct answers,
and saves them as Parquet files for each language.

The script takes three command-line arguments:
1. The directory containing the input prompt files.
2. The directory where the output Parquet files will be saved.
3. A comma-separated list of languages to process (optional, defaults to a predefined list).

Example usage:
python create_hf_datasets.py /path/to/input /path/to/output "en,es,fr"

To upload the generated Parquet files to Hugging Face:
1. Log in using `huggingface-cli login`.
2. Use the `huggingface-cli upload` command:
   huggingface-cli upload <username>/prompts_llms <output_directory_of_this_script> --repo-type=dataset

For more details, refer to the Hugging Face documentation.
"""

import os
import sys
from pathlib import Path

import pandas as pd

# Default list of languages
default_languages = ["en", "cs", "es", "de", "it", "ja", "nl", "tr", "zh", "fr"]


# Parse command-line arguments
try:
    input_dir = Path(sys.argv[1])
except IndexError:
    input_dir = Path(os.getcwd()) / "in_multlingual_nov24/prompts"
    print("\nYou can pass the input directory as the first CLI argument!\n")

try:
    output_dir = Path(sys.argv[2])
except IndexError:
    output_dir = Path(os.getcwd()) / "hf_prompts/validation"
    print("\nYou can pass the output directory as the second CLI argument!\n")

try:
    languages_str = sys.argv[3]
    languages = languages_str.split(",")
except IndexError:
    languages = default_languages
    print("\nYou can pass a comma-separated list of languages as the third CLI argument!\n")

# Ensure the output directory exists
output_dir.mkdir(parents=True, exist_ok=True)

# Read in correct answers
correct_answer_file = input_dir / "correct_results.tsv"
correct_answers = pd.read_csv(
    correct_answer_file, sep="\t", names=["disease_name", "disease_id", "file_id"]
)
correct_answers.set_index("file_id", inplace=True)

# Process each language
for lang in languages:
    lang_out_dir = output_dir / lang
    lang_out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created directory {lang_out_dir}")
    lang_in_dir = input_dir / lang

    rows = []
    for file in lang_in_dir.iterdir():
        # Extract file ID and match with correct answers
        file_ending = "en-prompt"
        file_id = file.stem[: -len(file_ending)] + file_ending + ".txt"
        gold_dict = {
            "disease_name": (
                correct_answers.loc[file_id, "disease_name"]
                if file_id in correct_answers.index
                else None
            ),
            "disease_id": (
                correct_answers.loc[file_id, "disease_id"]
                if file_id in correct_answers.index
                else None
            ),
        }

        # Read the prompt content
        with open(file, "r") as f:
            prompt = f.read()

        # Append the data to rows
        rows.append({"id": file.stem + ".txt", "prompt": prompt, "gold": gold_dict})

    # Save the DataFrame to a Parquet file
    df = pd.DataFrame(rows)
    out_file = lang_out_dir / f"{lang}_hf_prompts"
    df.to_parquet(out_file.with_suffix(".parquet"))
    print(f"Saved prompts to {out_file}.parquet")
