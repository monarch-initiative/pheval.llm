# Check grounding of replies by GPT
# Loop over replies, for each MONDO ID make dict entry with
# mondo_id: [gpt reply]
# it's an array, mondo id returns a list of labels, check how many non unique
# than put into df and add a third column with actual mondo_id and save to excel
import os

import pandas as pd

from pheval_llm.post_process.post_process_results_format import read_raw_result_yaml

filepath = (
    "/Users/leonardo/git/malco/out_multlingual_nov24/raw_results/multilingual/en/results.yaml"
)


if os.path.isfile(filepath):
    data = []

    all_results = read_raw_result_yaml(filepath)

    for this_result in all_results:
        extracted_object = this_result.get("extracted_object")
        ne = this_result.get("named_entities")
        if extracted_object and ne:
            label = extracted_object.get("label")
            gptinput = this_result.get("input_text")
            data.append({"label": label, "gpt_reply": gptinput, "grounded_response": ne})

df = pd.DataFrame(data, index=1)
df["gpt_reply"].iloc[0].rstrip().split("\n")
