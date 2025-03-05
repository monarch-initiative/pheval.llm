import csv

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
from seaborn import barplot

# Make a nice plot, use it as function or as script


def make_plots(mrr_file, data_dir, languages, num_ppkt, models, topn_aggr_file, comparing):
    plot_dir = data_dir.parents[0] / "plots"
    plot_dir.mkdir(exist_ok=True)

    # For plot filenam labeling use lowest number of ppkt available for all models/languages etc.
    num_ppkt = min(num_ppkt.values())

    if comparing == "model":
        name_string = str(len(models))
    else:
        name_string = str(len(languages))

    with mrr_file.open("r", newline="") as f:
        lines = csv.reader(f, quoting=csv.QUOTE_NONNUMERIC, delimiter="\t", lineterminator="\n")
        results_files = next(lines)
        mrr_scores = next(lines)

    print(results_files)
    print(mrr_scores)

    # Plotting the mrr results
    barplot(x=results_files, y=mrr_scores)
    plt.xlabel("Results File")
    plt.ylabel("Mean Reciprocal Rank (MRR)")
    plt.title("MRR of Correct Answers Across Different Results Files")
    plot_path = plot_dir / (name_string + "_" + comparing + "_" + str(num_ppkt) + "ppkt.png")
    plt.savefig(plot_path)
    plt.close()

    # Plotting bar-plots with top<n> ranks
    df_aggr = pd.read_csv(topn_aggr_file, delimiter="\t")

    plt.figure(figsize=(12, 6))
    plt.style.use("default")  # Set style to default

    ax = barplot(x="Rank_in", y="percentage", data=df_aggr, hue=comparing)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    plt.xlabel("")
    plt.ylabel("")
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=12)
    plt.ylim([0.0, 100])
    leg = plt.legend(title=comparing, fontsize=12, title_fontsize="large")
    leg.set_title("Language")
    plot_path = plot_dir / (
        "barplot_" + name_string + "_" + comparing + "_" + str(num_ppkt) + "ppkt.png"
    )
    plt.savefig(plot_path)
    plt.close()
