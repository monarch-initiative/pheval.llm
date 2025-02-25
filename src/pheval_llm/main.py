import click
import yaml
from pheval_llm.config import PhevalLLMConfig
from pheval_llm.post_process.post_process import post_process
from pheval_llm.post_process.ranking_utils import compute_mrr_and_ranks
from pheval_llm.post_process.generate_plots import make_plots


@click.group()
def core():
    pass

@core.command()
def format(config: str):
    """Takes some parameters from a combined results file and formats them into a pheval llm runner file"""
    return None

@core.command()
@click.option("--config", type=click.Path(exists=True))
def run(config: str):
    """Grounds, Evaluates, and Visualizes the results of an llm results file"""
    run_config = PhevalLLMConfig(config)

    post_process(run_config)

    if self.modality == "several_languages":
        comparing = "language"
        out_subdir = "multilingual"
    elif self.modality == "several_models":
        comparing = "model"
        out_subdir = "multimodel"
    else:
        raise ValueError("Not permitted run modality!\n")

    mrr_file, data_dir, num_ppkt, topn_aggr_file = compute_mrr_and_ranks(
        comparing,
        output_dir=run_config.output_dir,
        out_subdir=out_subdir,
        prompt_dir=os.path.join(run_config.input_dir, prompts_subdir_name),
        correct_answer_file=correct_answer_file,
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
    return None

cli = click.CommandCollection(sources=[core])
if __name__ == '__main__':
    core()