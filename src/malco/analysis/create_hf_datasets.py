import os 
import csv
from pathlib import Path
import pandas as pd

# After running this file, to upload to hf use something like:
# huggingface-cli login
# huggingface-cli upload leokim-l/prompts_llms hf_prompts/ --repo-type=dataset

languages = ['en', 'cs', 'es', 'de', 'it', 'ja', 'nl', 'tr', 'zh']

base_dir = Path(os.getcwd())
out_dir = base_dir / 'hf_prompts/validation' 
out_dir.mkdir(parents=True, exist_ok=True)

input_dir = base_dir / 'in_multlingual_nov24/prompts'
print(input_dir)

# Read in correct answers
correct_answer_file = input_dir / 'correct_results.tsv'
correct_answers = pd.read_csv(correct_answer_file, sep='\t', names=['disease_name', 'disease_id', 'file_id'])
correct_answers.set_index('file_id', inplace=True)

for lang in languages:
    lang_out_dir = out_dir / lang
    lang_out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created directory {lang_out_dir}")
    lang_in_dir = input_dir / lang

    # iterate through files and create dataframe
    rows = []
    for i, file in enumerate(lang_in_dir.iterdir()):
        file_ending = "en-prompt"
        file_id = file.stem[:-len(file_ending)] + file_ending + '.txt'
        gold_dict = {
            'disease_name': correct_answers.loc[file_id, 'disease_name'] if file_id in correct_answers.index else None,
           'disease_id': correct_answers.loc[file_id, 'disease_id'] if file_id in correct_answers.index else None
        }
        with open(file, 'r') as f:
            prompt = f.read()

        rows.append({'id': file.stem+'.txt', 'prompt': prompt, 'gold': gold_dict})
    
    # save dataframe to file
    df = pd.DataFrame(rows)
    out_file = lang_out_dir / f'{lang}_hf_prompts'
    df.to_parquet(out_file.with_suffix('.parquet'))

    print(f"Saved prompts to {out_file}.parquet")