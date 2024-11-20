from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree
from pheval.runners.runner import PhEvalRunner

from malco.post_process.ranking_utils import compute_mrr_and_ranks
from malco.post_process.post_process import post_process
from malco.run.run import run
from malco.prepare.setup_phenopackets import setup_phenopackets
from malco.prepare.setup_run_pars import import_inputdata
from malco.post_process.generate_plots import make_plots
import os


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
            run(self,
                )
            # Cleanup
            tmp_dir = f"{self.input_dir}/prompts/tmp/"
            if os.path.isdir(tmp_dir):
                rmtree(tmp_dir)

    def post_process(self,
                     print_plot=True,
                     prompts_subdir_name="prompts",
                     correct_answer_file="correct_results.tsv"
                     ):
        """
        Post-process the raw output into PhEval standardised TSV output.
        """
        if self.do_postprocess_step:
            print("post processing results to PhEval standardised TSV output.")

            post_process(self)

            if self.modality == "several_languages":
                comparing = "language"
                out_subdir = "multilingual"
            elif self.modality == "several_models":
                comparing = "model"
                out_subdir = "multimodel"
            else:
                raise ValueError('Not permitted run modality!\n')

            mrr_file, data_dir, num_ppkt, topn_aggr_file = compute_mrr_and_ranks(comparing,
                                                                                 output_dir=self.output_dir,
                                                                                 out_subdir=out_subdir,
                                                                                 prompt_dir=os.path.join(
                                                                                     self.input_dir, prompts_subdir_name),
                                                                                 correct_answer_file=correct_answer_file)

            if print_plot:
                make_plots(mrr_file, data_dir, self.languages, num_ppkt, self.models, topn_aggr_file, comparing)
