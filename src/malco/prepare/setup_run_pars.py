# setup_run_pars
import csv
import sys


def import_inputdata(self) -> None:
    """
    Example input file is located in ``self.input_dir`` and named run_parameters.csv
    It should contain something like:
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    "en"
    "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"
    1, 0
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Meaning run english prompts with those 4 aforementioned models, and only execute the run function,
    not postprocess.

    Or something like:
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    "en", "es", "nl", "it", "de"
    "gpt-4"
    0, 1
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    Meaning run multilingual prompts with those 5 aforementioned languages,
    and only execute the function postprocess, not run.
    """
    with open(self.input_dir / "run_parameters.csv", "r") as pars:
        lines = csv.reader(pars, quoting=csv.QUOTE_NONNUMERIC, delimiter=",", lineterminator="\n")
        in_langs = next(lines)
        in_models = next(lines)
        in_what_to_run = next(lines)

    ll = len(in_langs)
    m = len(in_models)
    if ll > 1 and m > 1:
        sys.exit("Error, either run multiple languages or models, not both, exiting...")
    elif ll == 1 and m >= 1:
        if in_langs[0] == "en":
            self.modality = (
                "several_models"  # English and more than 1 model defaults to multiple models
            )
        else:
            if m > 1:
                sys.exit("Error, only English and multiple models supported, exiting...")
            else:  # m==1
                self.modality = "several_languages"  # non English defaults to "multiple" languages mode
    elif ll > 1:
        self.modality = "several_languages"

    self.languages = tuple(in_langs)
    self.models = tuple(in_models)
    self.do_run_step = in_what_to_run[0]  # only run the run part of the code
    self.do_postprocess_step = in_what_to_run[1]  # only run the postprocess part of the code
