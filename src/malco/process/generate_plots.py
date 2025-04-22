import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from malco.model.language import Language
def make_single_plot(model_name, df, out_dir):
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
    plot_dir = out_dir / "plots"
    plot_dir.mkdir(exist_ok=True)
    plt.clf()
    df = pd.DataFrame(df.apply(_percentages, axis=1).tolist(),
                         columns=['Top-1', 'Top-3', 'Top-10', 'Model']).sort_values(by='Top-1', ascending=False)

    df.set_index('Model', inplace=True)
    df = df.T
    ax = df.plot(kind='bar', color=palette_hex_codes,
                    ylabel='Percent of cases', legend=True,
                    edgecolor="white", title="Top-k accuracy of correct diagnoses")
    # Make x-axis labels horizontal
    plt.xticks(rotation=0)
    # Move legend outside of figure
    # ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.ylim(0, 100)
    plt.savefig(plot_dir / f'{model_name}.png', bbox_inches='tight')
    plt.close()

def make_single_plot_from_file(model_name, topn_aggr_file, out_dir):
    df_aggr = pd.read_csv(topn_aggr_file, delimiter="\t").assign(filename=model_name)
    make_single_plot(model_name, df_aggr, Path(out_dir))

def make_combined_plot_comparing(results_dir, out_dir, model, langs):
    """Make a combined plot comparing the results of different models or languages"""
    # TODO: make this more adaptable for languages
    languages = [Language.from_short_name(lang) for lang in langs]
    glob = glob_generator(model, languages)
    results = pd.concat(
        [pd.read_csv(file, delimiter="\t").assign(filename=file.stem.replace("topn_result_", "")) for file in results_dir.glob(glob)],
        ignore_index=True
    )

    output_name = f"topn_{"grouped" if model == "*" else model}_{'' if languages[0] == Language.EN else languages[0].name.lower() if len(languages) == 1 else 'v'.join([lang.name.lower() for lang in languages])}.plot"
    make_single_plot(output_name, results, out_dir)

def _percentages(row):
    model_name = row['filename']
    total_files = row.drop('filename').drop('n10p').sum()
    return [
        row['n1'] / total_files * 100 if total_files else 0,
        sum(row[f'n{j}'] for j in range(1, 4)) / total_files * 100 if total_files else 0,
        sum(row[f'n{j}'] for j in range(1, 11)) / total_files * 100 if total_files else 0,
        model_name
    ]

def glob_generator(model: str, languages: list):
    """
        Generate glob pattern for file search based on model and languages.
        model: * or a specific file model name
        languages: List of Language enumerations
    """
    if len(languages) == 1:
        if languages[0] == Language.EN:
            return f"topn_result_{model}.tsv"
        elif languages[0] == Language.ALL:
            return f"topn_result_*_{model}.tsv"
        else:
            return f"topn_result_{languages[0].name.lower()}-{model}.tsv"
    else:
        return f"topn_result_{{{','.join([lang.name.lower() for lang in languages])}}}_{model}_*.tsv"