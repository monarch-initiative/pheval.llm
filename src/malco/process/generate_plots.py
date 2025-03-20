import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

def make_single_plot(model_name, df, out_dir):
    plot_dir = out_dir / "plots"
    plot_dir.mkdir(exist_ok=True)
    total_files = df.iloc[0].sum()

    plt.figure(figsize=(12, 6))
    plt.style.use("default")  # Set style to default

    # Generate the plot
    hits = ['Top-1', 'Top-3', 'Top-10']
    percentages = [
        df.at[0, 'n1'] / total_files * 100 if total_files else 0,
        sum(df.at[0, f'n{i}'] for i in range(1, 4)) / total_files * 100 if total_files else 0,
        sum(df.at[0, f'n{i}'] for i in range(1, 11)) / total_files * 100 if total_files else 0,
    ]
    plt.figure(figsize=(10, 6))
    plt.bar(hits, percentages, color=['blue', 'green', 'orange'], linewidth=0, align='center')
    plt.xlabel('Hits')
    plt.ylabel('Percent of cases')
    plt.title('Top-k accuracy of correct diagnoses')
    plt.ylim(0, 100)  # Adjust this as needed
    plt.savefig(plot_dir / f'{model_name}.png')
    plt.close()

def make_single_plot_from_file(model_name, topn_aggr_file, out_dir):
    # Plotting bar-plots with top<n> ranks
    df_aggr = pd.read_csv(topn_aggr_file, delimiter="\t").assign(filename=model_name)
    make_single_plot(model_name, df_aggr, Path(out_dir))

def make_combined_plot_comparing(results_dir, out_dir):
    """Make a combined plot comparing the results of different models or languages"""
    plt.clf()
    palette_hex_codes = [
        "#f4ae3d",
        "#ee5825",
        "#2b7288",
        "#9a84b2",
        "#0c604c",
        "#c94c4c",
        "#3d8e83",
        "#725ac1",
        "#e7ba52",
        "#1b9e77",
    ]

    plot_dir = Path(out_dir) / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)
    # Read in the results from each file in the results directory
    # TODO: make this more adaptable for languages
    results = pd.concat(
        [pd.read_csv(file, delimiter="\t").assign(filename=file.stem.replace("topn_result_", "")) for file in results_dir.glob("*.tsv")],
        ignore_index=True
    )

    topdf = pd.DataFrame(results.apply(_percentages, axis=1).tolist(),
                          columns=['Top-1', 'Top-3', 'Top-10', 'Model']).sort_values(by='Top-1', ascending=False)

    topdf.set_index('Model', inplace=True)
    topdf = topdf.T
    ax = topdf.plot(kind='bar', color = palette_hex_codes,
                         ylabel = 'Percent of cases', legend=True,
                         edgecolor = "white", title="Top-k accuracy of correct diagnoses")
    # Make x-axis labels horizontal
    plt.xticks(rotation=0)
    # Move legend outside of figure
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.ylim(0, 100)
    plt.savefig(plot_dir / f'grouped_plot.png', bbox_inches='tight')
    plt.close()

def _percentages(row):
    model_name = row['filename']
    total_files = row.drop('filename').drop('n10p').sum()
    return [
        row['n1'] / total_files * 100 if total_files else 0,
        sum(row[f'n{j}'] for j in range(1, 4)) / total_files * 100 if total_files else 0,
        sum(row[f'n{j}'] for j in range(1, 11)) / total_files * 100 if total_files else 0,
        model_name
    ]
