import click
from .config import PhevalLLMConfig
# from .post_process.post_process import post_process
from .post_process.ranking_utils import compute_mrr_and_ranks
from .post_process.generate_plots import make_plots


@click.group()
def core():
    pass

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
    run_config = PhevalLLMConfig(config)

    # post_process(run_config)
    modality = ""
    if modality == "several_languages":
        comparing = "language"
        out_subdir = "multilingual"
    elif modality == "several_models":
        comparing = "model"
        out_subdir = "multimodel"
    else:
        raise ValueError("Not permitted run modality!\n")

    # This piece of work is complex across "multiple models" & "multiple languages". We need to simplify this to a piece of work like in the notebook
    # our gold standard file needs a proper format one similar to a hugging face dataset. prompt, identifier, gold
    mrr_file, data_dir, num_ppkt, topn_aggr_file = compute_mrr_and_ranks(
        comparing,
        output_dir=run_config.output_dir,
        out_subdir=out_subdir,
        correct_answer_file=run_config.gold_file,
    )

    if run_config.visualize:
        make_plots(
            mrr_file,
            data_dir,
            run_config.languages,
            num_ppkt,
            run_config.models,
            topn_aggr_file,
            comparing,
        )

@core.command()
@click.option("--config", type=click.Path(exists=True))
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