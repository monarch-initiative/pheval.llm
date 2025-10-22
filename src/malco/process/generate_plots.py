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
    legend_title: str = "Models",
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

    # Get total cases from the first row (they're identical across all files)
    total_cases = df.loc[0, ["n1", "n2", "n3", "n4", "n5", "n6", "n7", "n8", "n9", "n10", "n10p", "nf"]].sum()
        
    # Add case count to title
    title_with_n = f"{title}, n={total_cases}"

    df = pd.DataFrame(
        df.apply(_percentages, axis=1).tolist(), columns=["Top-1", "Top-3", "Top-10", comparing]
    ).sort_values(by="Top-1", ascending=False)

    df.set_index(comparing, inplace=True)
    df = df.T
    ax = df.plot(
        kind="bar",
        color=palette_hex_codes,
        ylabel="%",
        legend=False,  # Disable automatic legend
        edgecolor="white",
        title=title_with_n,
    )
    plt.xticks(rotation=0)
    plt.ylim(0, 100)

    # Add legend outside the plot area with HPO range as title
    legend = ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    legend.set_title(legend_title)

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

    # Extract HPO range from first file for legend title
    title = "Top-k accuracy of correct diagnoses\n"  # Default
    if files:
        first_file_stem = files[0].stem
        if "_HPO_" in first_file_stem:
            # Extract range like "topn_result_6_10_HPO_model" -> "6_10"
            hpo_part = first_file_stem.split("_HPO_")[0].replace("topn_result_", "")
            hpo_range = hpo_part.replace("_", "-")
            # Convert range like "6-10" to "6 ≤ HPOs ≤ 10"
            if "-" in hpo_range:
                parts = hpo_range.split("-")
                if len(parts) == 2:
                    title = f"{title} {parts[0]} ≤ HPOs ≤ {parts[1]}"
            elif hpo_range.endswith("+"):
                # Handle 50+ case
                num = hpo_range[:-1]
                title = f"{title} HPOs ≥ {num}"
        elif "neurological" in first_file_stem.lower():
            title = f"{title} neurological features"
        elif "cardiovascular" in first_file_stem.lower():
            title = f"{title} cardiovascular features"
        elif "immunological" in first_file_stem.lower():
            title = f"{title} immunological features"
        elif "common" in first_file_stem.lower():
            title = f"{title} prevalence > 1 / 1M"
        elif "rare" in first_file_stem.lower():
            title = f"{title} prevalence < 1 / 1M"

            
    # Check if out_dir is file or directory path.
    if out_dir.suffix:
        output_name = out_dir.name
        plot_dir = out_dir.parent
    else:
        # Generate an output name and use out_dir as the directory
        output_name = f"topn_{'grouped' if model == '*' else model}_{'' if languages[0] == Language.EN else languages[0].name.lower() if len(languages) == 1 else 'v'.join([lang.name.lower() for lang in languages])}.png"
        plot_dir = out_dir / "plots"

    make_single_plot(output_name, results, plot_dir, comparing, title=title)


def _percentages(row):
    model_name = row["filename"]
    if "num_cases" in row.index and pd.notna(row["num_cases"]):
        total_files = row["num_cases"]
    else:
        # Calculate total sum from n1-n10 + n10p + nf columns
        total_files = (
            sum(row[f"n{j}"] for j in range(1, 11)) + row.get("n10p", 0) + row.get("nf", 0)
        )
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
            # Handle HPO-specific naming pattern: topn_result_*_HPO_{model}.tsv
            # Also handle disease category pattern: topn_result_{category}_{model}.tsv
            if model == "*":
                # When model is *, get all HPO files regardless of hyphens
                hpo_files = list(results_dir.glob(f"topn_result_*_HPO_*.tsv"))
                # Also look for disease category files: topn_result_{category}_{model}.tsv
                disease_files = list(results_dir.glob(f"topn_result_*_*.tsv"))
                # Filter out HPO files from disease files to avoid duplicates
                disease_files = [f for f in disease_files if "_HPO_" not in f.name]
                return hpo_files + disease_files
            else:
                # For specific models, use the hyphen filtering logic
                hpo_files = [
                    file
                    for file in list(results_dir.glob(f"topn_result_*_HPO_{model}.tsv"))
                    if "-" not in str(file) or str(file).count("-") == str(model).count("-")
                ]
                # Also look for disease category files with specific model
                disease_files = [
                    file
                    for file in list(results_dir.glob(f"topn_result_*_{model}.tsv"))
                    if "_HPO_" not in file.name
                    and ("-" not in str(file) or str(file).count("-") == str(model).count("-"))
                ]
                return hpo_files + disease_files
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
        # Handle both standard format and HPO format
        cleaned_stem = stem.replace("topn_result_", "")

        # Check if this is an HPO format file (contains _HPO_)
        if "_HPO_" in cleaned_stem:
            # Extract only the model name after _HPO_
            parts = cleaned_stem.split("_HPO_")
            model_name = parts[1]
            return model_name
        elif "neurological" in cleaned_stem.lower():
            parts = cleaned_stem.split("neurological")
            model_name = parts[1].lstrip("_")
            return model_name
        elif "cardiovascular" in cleaned_stem.lower():
            parts = cleaned_stem.split("cardiovascular")
            model_name = parts[1].lstrip("_")
            return model_name
        elif "immunological" in cleaned_stem.lower():
            parts = cleaned_stem.split("immunological")
            model_name = parts[1].lstrip("_")
            return model_name
        elif "rare" in cleaned_stem.lower():
            parts = cleaned_stem.split("rare")
            model_name = parts[1].lstrip("_")
            return model_name
        elif "common" in cleaned_stem.lower():
            parts = cleaned_stem.split("common")
            model_name = parts[1].lstrip("_")
            return model_name
        else:
            # Standard format
            return cleaned_stem
