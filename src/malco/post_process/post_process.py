from malco.post_process.post_process_results_format import create_standardised_results


def post_process(self) -> None:
    """
    Post-process the raw results output to standardised PhEval TSV format.

    Args:
        raw_results_dir (Path): Path to the raw results directory.
        output_dir (Path): Path to the output directory.
    """
    raw_results_dir = self.raw_results_dir
    output_dir = self.output_dir
    langs = self.languages
    models = self.models
    curategpt = True

    if self.modality == "several_languages":
        for lang in langs:
            raw_results_lang = raw_results_dir / "multilingual" / lang
            output_lang = output_dir / "multilingual" / lang
            raw_results_lang.mkdir(exist_ok=True, parents=True)
            output_lang.mkdir(exist_ok=True, parents=True)

            create_standardised_results(
                curategpt,
                raw_results_dir=raw_results_lang,
                output_dir=output_lang,
                output_file_name="results.tsv",
            )

    elif self.modality == "several_models":
        for model in models:
            raw_results_model = raw_results_dir / "multimodel" / model
            output_model = output_dir / "multimodel" / model
            raw_results_model.mkdir(exist_ok=True, parents=True)
            output_model.mkdir(exist_ok=True, parents=True)

            create_standardised_results(
                curategpt,
                raw_results_dir=raw_results_model,
                output_dir=output_model,
                output_file_name="results.tsv",
            )
