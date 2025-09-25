import ast
import json
import multiprocessing as mp
import os
import re
from pathlib import Path
from typing import Optional

import click
import litellm
import numpy as np
import pandas as pd

from .config import MalcoConfig
from .io.reading import read_result_json
from .process.generate_plots import (
    make_combined_plot_comparing,
    make_single_plot,
    make_single_plot_from_file,
)
from .process.process import create_single_standardised_results
from .process.scoring import mondo_adapter, score
from .process.summary import summarize

# Suppress debug info from litellm
litellm.suppress_debug_info = True


@click.group()
def core():
    pass


@core.command()
@click.option("--model", type=click.Choice(["gpt-4o", "claude-3", "llama-3.2"]), default="gpt-4o")
@click.option(
    "--key_file", type=click.Path(exists=True), default=os.path.expanduser("~/openai.key")
)
@click.option("--inputdir", type=click.Path(exists=True), default="test_inputdir/prompts/en")
@click.option("--outputdir", type=click.Path(exists=True), default="test_outputdir/")
def inference(model: str, key_file: str, inputdir: str, outputdir: str):
    """Runs one or multiple inferences on a set of prompts"""

    with open(key_file, "r") as key_file:
        api_key = key_file.read().strip()
        if model.startswith("gpt-"):
            env_var = "OPENAI_API_KEY"
            path = "openai"  # TODO generalize for other models
        elif model.startswith("claude-"):
            env_var = "ANTHROPIC_API_KEY"
        elif model.startswith("llama-"):
            env_var = "OLLAMA_API_KEY"
        else:
            raise ValueError("Model must be one of: gpt-4o, claude-3, llama-3.2")
    # Set the environment variable for the API key
    if env_var not in os.environ:
        print(f"Setting {env_var} environment variable for API key.")
        # Set the environment variable
        os.environ[env_var] = api_key

    # We suppose that next to the input directory we have a file named correct_results.tsv
    correct_results_file = os.path.join(os.path.dirname(inputdir), "correct_results.tsv")
    try:
        correct_results_df = pd.read_csv(
            correct_results_file, sep="\t", header=None, names=["disease_name", "disease_id", "id"]
        )
        correct_results_dict = {
            row["id"]: {"disease_id": row["disease_id"], "disease_name": row["disease_name"]}
            for _, row in correct_results_df.iterrows()
        }
    except FileNotFoundError:
        print(f"Warning: {correct_results_file} not found. 'gold' will be empty.")
        correct_results_dict = {}

    # Create the output file path in the output directory
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)
    output_file_path = os.path.join(outputdir, f"{model}.jsonl")

    # Iteratively prompt the model with all files in the input directory
    for filename in os.listdir(inputdir):
        if filename.endswith(".txt"):  # Process only text files
            input_file_path = os.path.join(inputdir, filename)

            # Read the content of the input file
            with open(input_file_path, "r") as infile:
                prompt_content = infile.read()

            # Prompt the model
            try:
                response = litellm.completion(
                    model=os.path.join(path, model),
                    messages=[{"content": prompt_content, "role": "user"}],
                )
                # Save the response to the output file as jsonl
                gold_value = correct_results_dict.get(filename, "")

                response_data = {
                    "id": filename,
                    "prompt": prompt_content,
                    "gold": gold_value,
                    "response": response.choices[0].message.content,
                }
                with open(
                    output_file_path, "a"
                ) as outfile:  # TODO careful not to overwrite files, change something here
                    json.dump(response_data, outfile)
                    outfile.write("\n")  # Add a newline to separate JSON objects in .jsonl format
            except Exception as e:
                print(f"Error processing {filename}: {e}")


@core.command()
@click.option("--config", type=click.Path(exists=True))
def evaluate(config: str):
    """Grounds, Evaluates, and Visualizes the results of a llm results file"""
    run_config = MalcoConfig(config)
    print(run_config)
    mondo_adapter()
    result = read_result_json(run_config.response_file)
    df = pd.DataFrame(
        {
            "service_answers": [x["response"] for x in result],
            "metadata": [x["id"] for x in result],
            "gold": [x["gold"] for x in result],
        }
    )
    cores = mp.cpu_count()
    if df.shape[0] < cores:
        cores = df.shape[0]
    chunks = np.array_split(df, cores)
    print(f"Running with {cores} cores\n")
    with mp.Pool(cores) as pool:
        results = pool.map(
            evaluate_chunk, [(index, chunk, run_config) for index, chunk in enumerate(chunks)]
        )
    df = pd.concat(results, ignore_index=True)
    df = score(df)
    Path(run_config.full_result_file).parent.mkdir(parents=True, exist_ok=True)
    df.drop("service_answers", axis=1).to_csv(run_config.full_result_file, sep="\t", index=False)
    print(f"Full results saved to {run_config.full_result_file}")
    print("\nComputing Statistics...\n")
    summarize(df, run_config)
    if run_config.visualize:
        print("Visualizing...\n")
        df["filename"] = run_config.name
        make_single_plot(run_config.name, df, run_config.output_dir)
    print("Done.")


@core.command()
@click.option("--config", type=click.Path(exists=True))
@click.option(
    "-oo",
    "--altpath",
    type=click.Path(),
    default=None,
    help="Alternative output directory and file",
)
@click.option(
    "--cases",
    type=click.Path(exists=True),
    default="data/results/multilingual_main/gpt-4o/ppkts_4917set.txt",
)
def select(config: str, cases: str, altpath: Optional[str]) -> None:
    """
    Selects the subset of phenopackets listed in the file `cases` and runs summarize on those only.
    Currently only supports the file IDs used for prompts.
    Args:
        config (str): Path to the configuration file.
        cases (str): Path to the file containing the phenopacket IDs or absolute paths to JSON files to select.
        altpath (Optional[str]): Alternative output directory and file path.
    Examples:
        malco select --config data/config/defaults.yaml --cases data/results/my_favorite_phenopacket_set.txt
    """
    run_config = MalcoConfig(config)
    if altpath is not None:
        run_config.result_file = altpath
    df = pd.read_csv(run_config.full_result_file, sep="\t")
    for col in ["gold", "grounding", "scored"]:
        df[col] = df[col].apply(ast.literal_eval)
    # Open the cases text file
    with open(cases, "r") as f:
        # Read the lines, strip whitespace and remove last n characters
        lines = [line.strip() for line in f.readlines()]
        if lines[0].endswith(".json"):
            # Handle list of json files by reading their ID and converting to prompt filename format
            regex_lines = []
            for json_file_path in lines:
                try:
                    with open(json_file_path.strip(), "r") as json_file:
                        ppkt_data = json.load(json_file)
                        ppkt_id = ppkt_data.get("id", "unknown")
                        modified_name = re.sub(r"[^\w]", "_", ppkt_id) + "_en-prompt.txt"
                        regex_lines.append(re.escape(modified_name))
                except Exception as e:
                    print(f"Warning: Could not process JSON file {json_file_path}: {e}")
                    continue
        elif re.search(r"_[a-z][a-z]-prompt\.txt$", lines[0]):
            n = len("_en-prompt.txt")
            regex_lines = [re.escape(line[:-n]) + r"_[a-z][a-z]-prompt\.txt" for line in lines]
        else:
            raise ValueError(
                "The cases file must contain either a list of json files or a list of prompt file name IDs."
            )

    # Filter the DataFrame based on the lines in the cases file
    # It is sufficient for the lines to be a substring of the metadata (to match all languages)
    df = df[df["metadata"].str.contains("|".join(regex_lines), regex=True)]
    # Save the counts of the filtered DataFrame to file
    summarize(df, run_config)


def evaluate_chunk(args) -> pd.DataFrame:
    process, df, run_config = args
    try:
        return create_single_standardised_results(df, process)
    except Exception as e:
        # Handle pickling issues with complex exception objects in multiprocessing
        error_str = str(e)
        error_type = type(e).__name__

        # Log the error and create a simple exception that can be pickled
        print(f"Error in process {process}: {error_type}: {error_str}")

        # For now, return an empty DataFrame with the same structure to avoid breaking the pipeline
        return pd.DataFrame({"service_answers": [], "metadata": [], "gold": [], "grounding": []})


@core.command()
@click.option(
    "--dir",
    type=click.Path(exists=True),
    help="Directory containing the scored differentials as tsv files you wish to combine.",
)
@click.option("--model", type=str, default="*", help="Model to compare, default is all [*].")
@click.option(
    "--lang",
    type=str,
    default="en",
    help="Language to compare, default is English [en]. If you don't care about languages, leave this empty.",
)
@click.option(
    "--outdir", type=str, default="data/results/", help="Directory where to save the resulting plot"
)
@click.option(
    "--comparing",
    type=Optional[str],
    default=None,
    help="What is being compared in the plot. If not provided, it will be automatically determined.",
)
def combine(dir: str, model: str, lang: str, outdir: str, comparing: Optional[str] = None) -> None:
    """
    Combines the results of several evaluate (or select) results into a single plot.
    We assume that non english languages have a hypen separating the model, and we want to filter these

    The files have to be named topn_result_{model}.tsv and the `model` cannot contain special characters like a "-"

    Args:
        dir (str): Directory containing the results files.
        model (str): Model to compare, can be "*" for all models or a specific model name.
        lang (str): Defaults to [en], if you do not care about languages leave the default.
            Alternatively, it can either be ALL, meaning all files in `dir`, or a
            comma-separated list of language codes to compare, e.g., "en,de" for English and German.
        outdir (str): Directory where the plot will be saved.
        comparing (str, optional): What is being compared in the plot. If not provided,
            it will be automatically determined as "Language" if comparing multiple
            languages, or "Model" otherwise.

    Examples:
        ### Compare all models in English
        malco combine --dir data/results --model "*" --lang en

        ### Compare gpt-4o across multiple languages
        malco combine --dir data/results --model gpt-4o --lang en,fr,de,es

        ### Compare gpt-4o in all available languages
        malco combine --dir data/results --model gpt-4o --lang ALL

        ### Compare with custom comparison label
        malco combine --dir data/results --model "*" --lang en --comparing "RAG type"
    """

    if model == "*" and lang == "ALL":
        raise ValueError("You must specify a single model to compare languages.")
    make_combined_plot_comparing(
        Path(dir), Path(outdir), model, lang.split(","), comparing=comparing
    )


@core.command()
@click.option("--config", type=click.Path(exists=True))
def plot(config: str):
    """Generates a plot from a results file"""
    run_config = MalcoConfig(config)
    make_single_plot_from_file(run_config.name, run_config.result_file, run_config.output_dir)


cli = click.CommandCollection(sources=[core])

if __name__ == "__main__":
    core()
