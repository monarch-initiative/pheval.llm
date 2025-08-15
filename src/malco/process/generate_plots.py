from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from malco.model.language import Language


def make_single_plot(
    model_name: str,
    df: pd.DataFrame,
    out_dir: Path,
    comparing: str = "Model",
    title: str = "Top-k accuracy of correct diagnoses",
) -> None:
    """
    Make a single plot from a DataFrame.

    Args:
        model_name (str): Name for the output file.
        df (pd.DataFrame): DataFrame containing the data to plot.
        out_dir (Path): Directory where the plot will be saved.
        comparing (str, optional): Column name that identifies what is being compared
            (e.g. "Model" or "Language"). Defaults to "Model".
        title (str, optional): Title of the plot. Defaults to "Top-k accuracy of correct diagnoses".
    """
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
    plot_dir = out_dir
    plot_dir.mkdir(exist_ok=True)
    plt.clf()
    df = pd.DataFrame(
        df.apply(_percentages, axis=1).tolist(), columns=["Top-1", "Top-3", "Top-10", comparing]
    ).sort_values(by="Top-1", ascending=False)

    df.set_index(comparing, inplace=True)
    df = df.T
    df.plot(
        kind="bar",
        color=palette_hex_codes,
        ylabel="Percent of cases",
        legend=True,
        edgecolor="white",
        title=title,
    )
    plt.xticks(rotation=0)
    plt.ylim(0, 100)
    plt.savefig(plot_dir / f"{model_name}", bbox_inches="tight")
    plt.close()


def make_single_plot_from_file(
    model_name: str, topn_aggr_file: str, out_dir: str, comparing: str = "Model"
) -> None:
    """
    Make a single plot from a file containing aggregated top-n results.

    Args:
        model_name (str): Name of the model.
        topn_aggr_file (str): Path to the file containing aggregated top-n results.
        out_dir (str): Directory where the plot will be saved.
        comparing (str, optional): Column name that identifies what is being compared.
            Defaults to "Model".
    """
    df_aggr = pd.read_csv(topn_aggr_file, delimiter="\t").assign(filename=model_name)
    make_single_plot(f"{model_name}.png", df_aggr, Path(out_dir), comparing)


def make_combined_plot_comparing(
    results_dir: Path, out_dir: Path, model: str, langs: list[str], comparing: str = None
) -> None:
    """
    Make a combined plot comparing the results of different models or languages.
    Args:
        results_dir (Path): Directory containing the results files.
        out_dir (Path): Directory where the plot will be saved. Can be either a directory
            path or a full file path (with filename).
        model (str): Model to compare, can be "*" for all models or a specific model name.
        langs (list[str]): List of language short names to compare, e.g., ["en", "de"].
        comparing (str, optional): What is being compared in this plot. If not provided,
            it will be automatically determined as "Language" if comparing multiple
            languages, or "Model" otherwise.
    """
    languages = [Language.from_short_name(lang) for lang in langs]
    files = glob_generator(model, languages, results_dir)
    if not files:
        raise ValueError(f"No matching files found for model={model} and languages={langs}")
    if comparing is None:
        comparing = "Language" if len(languages) > 1 else "Model"
    results = pd.concat(
        [
            pd.read_csv(file, delimiter="\t").assign(filename=stem_replacer(file.stem, languages))
            for file in files
        ],
        ignore_index=True,
    )

    # Check if out_dir is file or directory path.
    if out_dir.suffix:
        output_name = out_dir.name
        plot_dir = out_dir.parent
    else:
        # Generate an output name and use out_dir as the directory
        output_name = f"topn_{'grouped' if model == '*' else model}_{'' if languages[0] == Language.EN else languages[0].name.lower() if len(languages) == 1 else 'v'.join([lang.name.lower() for lang in languages])}.png"
        plot_dir = out_dir / "plots"

    make_single_plot(output_name, results, plot_dir, comparing)


def _percentages(row):
    model_name = row["filename"]
    if 'num_cases' in row.index and pd.notna(row['num_cases']):
        total_files = row["num_cases"]
    else:
        # Calculate total sum from n1-n10 + n10p + nf columns
        total_files = sum(row[f"n{j}"] for j in range(1, 11)) + row.get('n10p', 0) + row.get('nf', 0)
    return [
        row["n1"] / total_files * 100 if total_files else 0,
        sum(row[f"n{j}"] for j in range(1, 4)) / total_files * 100 if total_files else 0,
        sum(row[f"n{j}"] for j in range(1, 11)) / total_files * 100 if total_files else 0,
        model_name,
    ]


def glob_generator(model: str, languages: list[Language], results_dir: Path) -> list[Path]:
    """
    Generate glob pattern for file search based on model and languages.

    Args:
        model (str): Model identifier, use * for all models in `results_dir` or a specific file model name.
        languages (list[Language]): List of Language enumerations to filter results.
        results_dir (Path): Directory where the results files are located.

    Returns:
        list[Path]: List of Path objects matching the specified model and languages.
    """
    if len(languages) == 1:
        if languages[0] == Language.EN:
            # We assume that non english languages have a hypen separating the model, and we want to filter these
            return [
                file
                for file in list(results_dir.glob(f"topn_result_{model}.tsv"))
                if "-" not in str(file)
            ]
        elif languages[0] == Language.ALL:
            return list(results_dir.glob(f"topn_result_*-{model}.tsv"))
        else:
            return list(results_dir.glob(f"topn_result_{languages[0].name.lower()}-{model}.tsv"))
    else:
        return list(
            results_dir.glob(
                f"topn_result_{{{','.join([lang.name.lower() for lang in languages])}}}_{model}_*.tsv"
            )
        )


def stem_replacer(stem, languages):
    if Language.ALL in languages or len(languages) > 1:
        try:
            stem = Language.from_short_name(
                stem.replace("topn_result_", "").replace("_", "")[0:2].upper()
            ).value
        except Exception:
            stem = "English"
        return stem
    else:
        return stem.replace("topn_result_", "")
