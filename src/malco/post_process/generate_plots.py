import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import os
import csv

# Make a nice plot, use it as function or as script

def make_plots(mrr_file, data_dir, languages, num_ppkt, models, topn_aggr_file, comparing):
    plot_dir = data_dir.parents[0] / "plots"
    plot_dir.mkdir(exist_ok=True)

    # For plot filenam labeling use lowest number of ppkt available for all models/languages etc.
    num_ppkt = min(num_ppkt.values())

    if comparing=="model":
        name_string = str(len(models))
    else:
        name_string = str(len(languages))

    with mrr_file.open('r', newline = '') as f:
        lines = csv.reader(f, quoting = csv.QUOTE_NONNUMERIC, delimiter = '\t', lineterminator='\n')
        results_files = next(lines)
        mrr_scores = next(lines)
            
    print(results_files)
    print(mrr_scores)

    # Plotting the mrr results
    sns.barplot(x = results_files, y = mrr_scores)
    plt.xlabel("Results File")
    plt.ylabel("Mean Reciprocal Rank (MRR)")
    plt.title("MRR of Correct Answers Across Different Results Files")
    plot_path = plot_dir /  (name_string + "_" + comparing + "_" + str(num_ppkt) + "ppkt.png")
    plt.savefig(plot_path)
    plt.close()

    # Plotting bar-plots with top<n> ranks
    df_aggr = pd.read_csv(topn_aggr_file, delimiter='\t')
    
    sns.barplot(x="Rank_in", y="percentage", data = df_aggr, hue = comparing)

    plt.xlabel("Number of Ranks in")
    plt.ylabel("Percentage of Cases")
    plt.ylim([0.0, 1.0])
    plt.title("Rank Comparison for Differential Diagnosis")
    plt.legend(title=comparing)
    plot_path = plot_dir /  ("barplot_" + name_string + "_" + comparing + "_" + str(num_ppkt) + "ppkt.png")
    plt.savefig(plot_path)
    plt.close()
    
