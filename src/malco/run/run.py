# import multiprocessing
# import os
# import shutil
# import subprocess
# import typing
# from pathlib import Path
#
# from malco.run.search_ppkts import search_ppkts
#
#
# def call_ontogpt(
#     lang: str,
#     raw_results_dir: Path,
#     input_dir: Path,
#     model: str,
#     modality: typing.Literal["several_languages", "several_models"],
# ) -> None:
#     """
#     Wrapper used for parallel execution of ontogpt.
#
#     Args:
#         lang (str): Two-letter language code, for example "en" for English.
#         raw_results_dir (Path): Path to the raw results directory.
#         output_dir (Path): Path to the output directory.
#         model (str): Name of the model to be run, e.g. "gpt-4-turbo".
#         modality (str): Determines whether English and several models or gpt-4o and several languages are being run.
#
#     Returns:
#         None
#     """
#     prompt_dir = f"{input_dir}/prompts/"
#     if modality == "several_languages":
#         lang_or_model_dir = lang
#         prompt_dir += f"{lang_or_model_dir}/"
#     elif modality == "several_models":
#         lang_or_model_dir = model
#         prompt_dir += "en/"
#     else:
#         raise ValueError("Not permitted run modality!\n")
#
#     selected_indir = search_ppkts(input_dir, prompt_dir, raw_results_dir, lang_or_model_dir)
#     yaml_file = f"{raw_results_dir}/{lang_or_model_dir}/results.yaml"
#
#     if os.path.isfile(yaml_file):
#         old_yaml_file = yaml_file
#         yaml_file = f"{raw_results_dir}/{lang_or_model_dir}/new_results.yaml"
#         print(f"new yaml and old yaml of {model}are :")
#         print(yaml_file)
#         print(old_yaml_file)
#
#     command = (
#         f"ontogpt -v run-multilingual-analysis "
#         f"--output={yaml_file} "  # save raw OntoGPT output
#         f"{selected_indir} "
#         f"{raw_results_dir}/{lang_or_model_dir}/differentials_by_file/ "  # OntoGPT output directory
#         f"--model={model}"
#     )
#
#     print(f"Running command: {command}")
#     process = subprocess.Popen(command, shell=True)
#     process.communicate()
#
#     # Note: if file.txt.result is empty, what ends up in the yaml is still OK thanks
#     # to post_process_results_format.py
#     print(f"Finished command for language {lang} and model {model}")
#     try:
#         with open(yaml_file, "r") as file2concat:
#             with open(old_yaml_file, "a") as original_file:
#                 shutil.copyfileobj(file2concat, original_file)
#         os.remove(yaml_file)
#     except NameError:
#         pass
#     except FileNotFoundError:
#         pass
#
#
# def run(self, max_workers: int = None) -> None:
#     """
#     Run the tool to obtain the raw results.
#
#     Args:
#         testdata_dir: Path to the test data directory.
#         raw_results_dir: Path to the raw results directory.
#         output_dir: Path to the output directory.
#         langs: Tuple of languages.
#         max_workers: Maximum number of worker processes to use.
#     """
#     raw_results_dir = self.raw_results_dir
#     input_dir = self.input_dir
#     langs = self.languages
#     models = self.models
#     modality = self.modality
#
#     if max_workers is None:
#         max_workers = multiprocessing.cpu_count()
#
#     if modality == "several_languages":
#         with multiprocessing.get_context("spawn").Pool(processes=max_workers) as pool:
#             try:
#                 pool.starmap(
#                     call_ontogpt,
#                     [
#                         (lang, raw_results_dir / "multilingual", input_dir, models[0], modality)
#                         for lang in langs
#                     ],
#                 )
#             except FileExistsError as e:
#                 raise ValueError("Did not clean up after last run, check tmp dir: \n" + e)
#
#     if modality == "several_models":
#         # English only many models
#         with multiprocessing.get_context("spawn").Pool(processes=max_workers) as pool:
#             try:
#                 pool.starmap(
#                     call_ontogpt,
#                     [
#                         ("en", raw_results_dir / "multimodel", input_dir, model, modality)
#                         for model in models
#                     ],
#                 )
#             except FileExistsError as e:
#                 raise ValueError("Did not clean up after last run, check tmp dir: \n" + e)
