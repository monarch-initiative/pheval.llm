import os
from pathlib import Path
from shutil import rmtree

from pheval.runners.runner import PhEvalRunner

from malco.post_process.generate_plots import make_plots
from malco.post_process.post_process import post_process
from malco.post_process.ranking_utils import compute_mrr_and_ranks
from malco.prepare.setup_run_pars import import_inputdata
from malco.run.run import run


class MalcoRunner(PhEvalRunner):
    input_dir: Path
    testdata_dir: Path
    tmp_dir: Path
    output_dir: Path
    config_file: Path
    version: str

    def prepare(self):
        """
        Pre-process any data and inputs necessary to run the tool.
        """
        print("Preparing...\n")
        import_inputdata(self)

    def run(self):
        """
        Run the tool to produce the raw output.
        """
        print("running with predictor")
        pass
        if self.do_run_step:
            run(
                self,
            )
            # Cleanup
            tmp_dir = f"{self.input_dir}/prompts/tmp/"
            if os.path.isdir(tmp_dir):
                rmtree(tmp_dir)

    def post_process(
        self,
        print_plot=True,
        prompts_subdir_name="prompts",
        correct_answer_file="correct_results.tsv",
    ):
        """
        Post-process the raw output into PhEval standardised TSV output.
        """
        if self.do_postprocess_step: