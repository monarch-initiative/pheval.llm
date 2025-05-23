from malco.config import MalcoConfig
from tqdm import tqdm
import pandas as pd
from collections import Counter

def summarize(df, run_config: MalcoConfig):
    # Initialize the counter for each rank
    rank_counter = Counter()
    for index, row in tqdm(df.iterrows(), total=len(df)):
            correct_rank = None
            if row["scored"] is not None and len(row["scored"]) > 0:
                # array of results
                scored = pd.DataFrame(row["scored"])
                # Find the first occurrence of the correct diagnosis
                correct_rank = scored[scored['is_correct'] == True].index.min() + 1 if not scored[scored['is_correct'] == True].empty else None

            # Increment the appropriate counter based on the rank or nf if not found
            if correct_rank is not None and 1 <= correct_rank <= 10:
                rank_counter[f'n{correct_rank}'] += 1
            else:
                rank_counter['nf'] += 1

    # Get the total number of records processed
    total_files = sum(rank_counter.values())

    # Prepare the row to be written to the output file (without the 'lang' column)
    output_row = [
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
        rank_counter.get('n10', 0) / total_files if total_files else 0,  # n10p: proportion of n10 hits || TODO: fix this
        rank_counter.get('nf', 0)
    ]

    # Write the results to the output file (without 'lang' column)
    with open(f"{run_config.result_file}", 'w') as f:
        f.write('n1\tn2\tn3\tn4\tn5\tn6\tn7\tn8\tn9\tn10\tn10p\tnf\n')
        f.write('\t'.join(map(str, output_row)) + '\n')
    return True