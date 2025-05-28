from pathlib import Path

import click

from .config import MalcoConfig
from .process.scoring import score, mondo_adapter
from .process.generate_plots import make_single_plot_from_file, make_single_plot, make_combined_plot_comparing
from .process.process import create_single_standardised_results
from .process.summary import summarize
from .io.reading import read_result_json
import pandas as pd
import multiprocessing as mp
import numpy as np
import ast
import re

@click.group()
def core():
    pass

@core.command()
def inference():
    """Runs one or multiple inferences on a set of prompts"""
    # TODO: Implement this with ollama for local models and litellm for API based calls?
    return None

@core.command()
@click.option("--config", type=click.Path(exists=True))
def evaluate(config: str):
    """Grounds, Evaluates, and Visualizes the results of a llm results file"""
    run_config = MalcoConfig(config)
    print(run_config)
    mondo_adapter()
    result = read_result_json(run_config.response_file)
    df = pd.DataFrame({
        "service_answers": [x["response"] for x in result],
        "metadata":  [x["id"] for x in result],
        "gold": [x["gold"] for x in result]
    })
    cores = mp.cpu_count()
    if df.shape[0] < cores:
        cores = df.shape[0]
    chunks = np.array_split(df, cores)
    print(f"Running with {cores} cores\n")
    with mp.Pool(cores) as pool:
        results = pool.imap_unordered(evaluate_chunk, [(index, chunk, run_config) for index, chunk in enumerate(chunks)])
        results = list(results)
    df = pd.concat(results, ignore_index=True)
    df = score(df)
    df.drop('service_answers', axis=1).to_csv(run_config.full_result_file, sep="\t", index=False)
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
@click.option("--cases", type=click.Path(exists=True))
def select(config: str, cases: str):
    """Selects a subset of phenopackets to run summarize on."""
    run_config = MalcoConfig(config)
    df = pd.read_csv(run_config.full_result_file, sep="\t")
    for col in ["gold", "grounding", "scored"]:
        df[col] = df[col].apply(ast.literal_eval)
    # Open the cases text file
    with open(cases, 'r') as f:
        # Read the lines, strip whitespace and remove last n characters
        lines = [line.strip() for line in f.readlines()]
        if lines[0].endswith(".json"):
            pass
            # TODO add support for list of json files (which should/wuill be the primary use case)
        elif re.search(r"_[a-z][a-z]-prompt\.txt$", lines[0]):
            n = len("_en-prompt.txt")
            regex_lines = [re.escape(line[:-n]) + r"_[a-z][a-z]-prompt\.txt" for line in lines]
        else:
            raise ValueError("The cases file must contain either a list of json files or a list of phenopackets with the last n characters removed.")
        
    # Filter the DataFrame based on the lines in the cases file
    # It is sufficient for the lines to be a substring of the metadata (to match all languages)
    df = df[df['metadata'].str.contains('|'.join(regex_lines), regex=True)] 
    # Save the counts of the filtered DataFrame to file
    summarize(df, run_config) 


def evaluate_chunk(args) -> pd.DataFrame:
    process, df, run_config = args
    return create_single_standardised_results(df, process)

@core.command()
@click.option("--dir", type=click.Path(exists=True))
@click.option("--model", type=str, default="*", help="Model to compare, default is all [*].")
@click.option("--lang", type=str, default="en", help="Language to compare, default is English [en].")
@click.option("--outdir", type=str, default="data/results/", help="Where to save the resulting plot")
def combine(dir: str, model: str, lang: str, outdir: str):
    """Combines the results of several evaluate results into a single plot"""
    if model == "*" and lang == "ALL":
        raise ValueError("You must specify a single model to compare languages.")
    make_combined_plot_comparing(Path(dir), Path(outdir), model, lang.split(","))

@core.command()
@click.option("--config", type=click.Path(exists=True))
def plot(config: str):
    """Generates a plot from a results file"""
    run_config = MalcoConfig(config)
    make_single_plot_from_file(run_config.name, run_config.result_file, run_config.output_dir)

cli = click.CommandCollection(sources=[core])

if __name__ == '__main__':
    core()
