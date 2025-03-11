import click
from .config import MalcoConfig
from .process.scoring import score, mondo_adapter
from .process.generate_plots import make_plots
from .process.process import create_single_standardised_results
from .process.summary import summarize
from .io.reading import read_result_json
import os
import pandas as pd
import multiprocessing as mp
import numpy as np

@click.group()
def core():
    pass

@core.command()
def configure():
    """Configures the malco tool"""
    # Read in OpenAI key file (for curategpt grounding)
    key_file_path = os.path.expanduser("~/openai.key")
    # Read the key from the file and set the environment variable
    with open(key_file_path, "r") as key_file:
        openai_api_key = key_file.read().strip()
    os.environ["OPENAI_API_KEY"] = openai_api_key
    print("Successfully configured malco.")

@core.command()
def format():
    """Takes some parameters from a combined results file and formats them into a pheval llm runner file"""
    # TODO: Ideally we settle on a format that evaluate reads (can be ontogpt yaml file format)
    # Example: Meditron code output jsonl file with prompt, gold, answer we can format this to the ontogpt yaml if we decide
    # Ideally in the future our inference pipeline generates this format and this command gets used less and less
    return None

@core.command()
def inference():
    """Runs one or multiple inferences on a set of prompts"""
    # TODO: Implement this with ollama?
    return None

@core.command()
@click.option("--config", type=click.Path(exists=True))
def evaluate(config: str):
    """Grounds, Evaluates, and Visualizes the results of an llm results file"""
    run_config = MalcoConfig(config)
    print(run_config)
    mondo_adapter()
    result = read_result_json(run_config.result_file)
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
    print("\nComputing Statistics...\n")
    summarize(df, run_config)
    if run_config.visualize:
        print("Visualizing...\n")
            # make_plots(
            #     mrr_file,
            #     data_dir,
            #     run_config.languages,
            #     num_ppkt,
            #     run_config.models,
            #     topn_aggr_file,
            #     comparing,
            # )
    print("Done.")

def evaluate_chunk(args) -> pd.DataFrame:
    process, df, run_config = args
    return create_single_standardised_results(df, process)

@core.command()
@click.option("--dir", type=click.Path(exists=True))
def combine():
    """Combines the results of several evaluate results into a single report"""
     # Cleanup
    # tmp_dir = f"{self.input_dir}/prompts/tmp/"
    # if os.path.isdir(tmp_dir):
    #     rmtree(tmp_dir)
    return None

cli = click.CommandCollection(sources=[core])

if __name__ == '__main__':
    core()