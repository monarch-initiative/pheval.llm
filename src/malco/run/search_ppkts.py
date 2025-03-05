import os
import shutil

from malco.process.post_process_results_format import read_raw_result_yaml


def search_ppkts(input_dir, prompt_dir, raw_results_dir, lang_or_model):
    """
    Check what ppkts have already been computed in current output dir, for current run parameters.

    ontogpt will run every .txt that is in inputdir, we need a tmp inputdir
    excluding already run cases. Source of truth is the results.yaml output by ontogpt.
    Only extracted_object containing terms is considered successfully run.

    Note that rerunning
    """

    # List of "labels" that are already present in results.yaml iff terms is not None
    files = []

    yaml_file = f"{raw_results_dir}/{lang_or_model}/results.yaml"
    if os.path.isfile(yaml_file):
        # tmp inputdir contains prompts yet to be computed for a given model (pars set)
        selected_indir = f"{input_dir}/prompts/tmp/{lang_or_model}"
        os.makedirs(selected_indir)

        all_results = read_raw_result_yaml(yaml_file)
        for this_result in all_results:
            extracted_object = this_result.get("extracted_object")
            if extracted_object:
                label = extracted_object.get("label")
                terms = extracted_object.get("terms")
                if terms:
                    # ONLY if terms is non-empty, it was successful
                    files.append(label)
    else:
        return prompt_dir

    # prompts: ls prompt_dir
    promptfiles = []
    for _dirpath, _dirnames, filenames in os.walk(prompt_dir):
        promptfiles.extend(filenames)
        break

    # foreach promptfile in original_inputdir
    for promptfile in promptfiles:
        # If something failed and an empty file exists, run it again
        # Copy all prompt files in the new tmp inputdir, except the ones of line above
        if promptfile in files:
            continue
        else:
            shutil.copyfile(prompt_dir + promptfile, selected_indir + "/" + promptfile)

    return selected_indir
