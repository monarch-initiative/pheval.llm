from malco.config import MalcoConfig
from tqdm import tqdm
import pandas as pd
from collections import Counter

def summarize(df, run_config: MalcoConfig):
    # Initialize the counter for each rank
    rank_counter = Counter()
    for index, row in tqdm(df.iterrows(), total=len(df)):
        correct_rank = None
        grounding_failure = None
        item_number = None
        if row["scored"] is not None and len(row["scored"]) > 0:
            rank_counter['nc'] += 1  # Count the number of cases processed
            # array of results
            scored = pd.DataFrame(row["scored"])
            # Find the first occurrence of the correct diagnosis
            correct_rank = scored[scored['is_correct'] == True].index.min() + 1 if not scored[scored['is_correct'] == True].empty else None
            grounding_failure = any(scored['grounded_id'] == 'N/A')
            # Get number of items in scored and save it in item_number
            item_number = len(scored)
        # Increment the appropriate counter based on the rank or nf if not found
        if correct_rank is not None and 1 <= correct_rank <= 10:
            rank_counter[f'n{correct_rank}'] += 1
        elif correct_rank is not None and correct_rank > 10:
            rank_counter['n10p'] += 1  # Increment n10p for ranks greater than 10
        else:
            rank_counter['nf'] += 1
        # If grounding_failure is True, also increase that counter 
        if grounding_failure is True:
            rank_counter['tgf'] += 1
            if correct_rank is None:
                rank_counter['gf'] += 1
        # Count all items processed
        if item_number is not None:
            rank_counter['items'] += item_number


    # Prepare the row to be written to the output file (without the 'lang' column)
    output_row = [
        run_config.name[0:2],  # run name
        rank_counter.get('n1', 0),
        rank_counter.get('n2', 0),
        rank_counter.get('n3', 0),
        rank_counter.get('n4', 0),
        rank_counter.get('n5', 0),
        rank_counter.get('n6', 0),
        rank_counter.get('n7', 0),
        rank_counter.get('n8', 0),
        rank_counter.get('n9', 0),
        rank_counter.get('n10', 0),
        rank_counter.get('n10p', 0),  # rank > 10
        rank_counter.get('nf', 0),
        rank_counter.get('gf', 0), # among the not found, how many involved a grounding failrue somewhere in the dx
        rank_counter.get('nc', 0), # total number of cases processed (count invalid replies by model, if any at all)
        rank_counter.get('tgf', 0), # total grounding failures
        rank_counter.get('items', 0)  # total items processed
    ]

    # Write the results to the output file (without 'lang' column)
    with open(f"{run_config.result_file}", 'w') as f:
        f.write('run\tn1\tn2\tn3\tn4\tn5\tn6\tn7\tn8\tn9\tn10\tn10p\tnf\tgrounding_failed\tnum_cases\ttotal_grounding_failures\titems_processed\n')
        f.write('\t'.join(map(str, output_row)) + '\n')
    return True