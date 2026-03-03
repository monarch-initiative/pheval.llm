"""This python script imports phenopackets from a directory and creates subsets based on the
number of observed HPO terms that they contain. Configuration is loaded from a YAML file."""

import os
import json
import yaml
from pathlib import Path
import argparse

# Get script directory to find config file
script_dir = Path(__file__).parent
parser = argparse.ArgumentParser(
    description="Given a config, generate a txt of phenopacket paths, usually a subset based on some rule."
)
parser.add_argument(
    "-c",
    "--config",
    type=str,
    default=script_dir / "phenopacket_subset_config.yaml",
    help="Path to configuration file",
)
parser.add_argument(
    "-i",
    "--input-path",
    type=str,
    default="~/data/phenopackets/",
    help="Path to input phenopackets directory",
)
parser.add_argument(
    "-ha",
    "--hpoa-file",
    type=str,
    default="~/data/phenotype.hpoa",
    help="Path to input phenopackets directory",
)


args = parser.parse_args()
config_file = Path(args.config)
input_path = args.input_path
hpoa_file = args.hpoa_file

hpoa_file = Path(hpoa_file).expanduser()
if not hpoa_file.exists():
    print(f"Error: HPOA file not found: {hpoa_file}")
    exit(1)

input_path = Path(input_path).expanduser()
if not input_path.exists():
    print(f"Error: Input path not found: {input_path}")
    exit(1)

# Load configuration
with open(config_file, "r") as f:
    config = yaml.safe_load(f)

# TODO make all writing into 1 function
# def write_results():


# Initialize info_file as None, will be set after output_dir is created
info_file = None


def print_and_log(message):
    """Print message to console and write to INFO.md file."""
    print(message)
    if info_file:
        with open(info_file, "a") as f:
            f.write(message + "\n")


# import all json files in the given directory and subdirectories
phenopackets = []
for root, dirs, files in os.walk(input_path):
    for filename in files:
        if filename.endswith(".json"):
            file_path = os.path.join(root, filename)
            with open(file_path, "r") as f:
                pkt_data = json.load(f)
                pkt_data["_filename"] = filename  # Store the original filename
                pkt_data["_absolute_path"] = os.path.abspath(file_path)  # Store absolute path
                phenopackets.append(pkt_data)

# Create output directory based on config
output_config = config["output"]
output_dir = os.path.join(output_config["base_dir"], output_config["config_name"])
os.makedirs(output_dir, exist_ok=True)

# Set up INFO.md file path and clear any existing content
info_file = os.path.join(output_config["base_dir"], output_config["config_name"], "INFO.md")
with open(info_file, "w") as f:
    f.write("# Phenopacket Subsets Creation Log\n\n")

# ----------- HPO BINS -----------
# Create bins based on configuration
if config["bins"]:
    hpo_bins = {bin_config["name"]: [] for bin_config in config["bins"]}

    for pkt in phenopackets:
        hpo_count = sum(
            1 for feature in pkt.get("phenotypicFeatures", []) if "excluded" not in feature
        )

        # Find which bin this phenopacket belongs to
        for bin_config in config["bins"]:
            min_hpos = bin_config["min_hpos"]
            max_hpos = bin_config["max_hpos"]

            if max_hpos is None:  # No upper limit
                if hpo_count >= min_hpos:
                    hpo_bins[bin_config["name"]].append(pkt)
                    break
            else:  # Has upper limit
                if min_hpos <= hpo_count <= max_hpos:
                    hpo_bins[bin_config["name"]].append(pkt)
                    break

    # print the number of phenopackets in each subset
    for bin_name, pkts in hpo_bins.items():
        print_and_log(f"Phenopackets in bin '{bin_name}': {len(pkts)}")

    # Write the json file absolute paths for each subset into a separate text file
    if config["write"]:
        print_and_log(f"Writing subset files to: {output_dir}")
        for bin_name, pkts in hpo_bins.items():
            filename = f"{output_config['file_prefix']}_{bin_name}{output_config['file_extension']}"
            with open(os.path.join(output_dir, filename), "w") as f:
                for pkt in pkts:
                    f.write(f"{pkt.get('_absolute_path', 'unknown')}\n")

# ----------- DISEASE CATEGORIES -----------
if config["categories"]:
    # This part creates subsets based on disease categories using HPO
    import hpotk
    from tqdm import tqdm

    store = hpotk.configure_ontology_store()
    hpo = store.load_hpo()  # TODO where does it look for this?

    HEART = hpo.get_term("HP:0001626")  #  Abnormality of the cardiovascular system
    BRAIN = hpo.get_term("HP:0000707")  # Abnormality of the nervous system
    IMMUNE = hpo.get_term("HP:0002715")  # Abnormality of the immune system

    disease_categories = {"cardiovascular": [], "neurological": [], "immunological": []}
    pkt_to_file = {pkt["id"]: pkt.get("_absolute_path", "unknown") for pkt in phenopackets}
    for pkt in tqdm(phenopackets, total=len(phenopackets)):
        ppkt_observed_features = [
            feature for feature in pkt.get("phenotypicFeatures", []) if "excluded" not in feature
        ]
        for feature in ppkt_observed_features:
            term_id = feature.get("type", {}).get("id")
            if term_id:
                term = hpo.get_term(term_id)
                if (
                    term
                    and hpo.graph.is_ancestor_of(HEART, term)
                    and pkt["id"] not in disease_categories["cardiovascular"]
                ):
                    disease_categories["cardiovascular"].append(pkt["id"])
                if (
                    term
                    and hpo.graph.is_ancestor_of(BRAIN, term)
                    and pkt["id"] not in disease_categories["neurological"]
                ):
                    disease_categories["neurological"].append(pkt["id"])
                if (
                    term
                    and hpo.graph.is_ancestor_of(IMMUNE, term)
                    and pkt["id"] not in disease_categories["immunological"]
                ):
                    disease_categories["immunological"].append(pkt["id"])
    # print the number of unique phenopackets in each disease category
    for category, pkts in disease_categories.items():
        print_and_log(f"Phenopackets in disease category '{category}': {len(set(pkts))}")
    # Print the size of the overlap between categories
    cardiovascular_set = set(disease_categories["cardiovascular"])
    neurological_set = set(disease_categories["neurological"])
    immunological_set = set(disease_categories["immunological"])
    print_and_log(
        f"Overlap between cardiovascular and neurological: {len(cardiovascular_set & neurological_set)}"
    )
    print_and_log(
        f"Overlap between cardiovascular and immunological: {len(cardiovascular_set & immunological_set)}"
    )
    print_and_log(
        f"Overlap between neurological and immunological: {len(neurological_set & immunological_set)}"
    )
    print_and_log(
        f"Overlap between all three: {len(cardiovascular_set & neurological_set & immunological_set)}"
    )

    # write the phenopacket json paths for each disease category into a separate text file
    if config["write"]:
        print_and_log(f"Writing disease category files to: {output_dir}")
        for category, pkts in disease_categories.items():
            filename = f"{output_config['file_prefix']}_{category}{output_config['file_extension']}"
            with open(os.path.join(output_dir, filename), "w") as f:
                for pkt in pkts:
                    f.write(f"{pkt_to_file.get(pkt, 'unknown')}\n")

# ----------- DISJUNCTIVE UNION HPOA AND STORE -----------
# Extract PMIDs from externalReferences

if config["hpoa"]:
    import pandas as pd

    hpoa_df = pd.read_csv(hpoa_file, header=4, sep="\t", usecols=["reference"])

    # TODO the regex will miss a few (very few!) entries in HPOA
    raw_hpoa_counts = (
        hpoa_df["reference"].str.extract(r"^([A-Z]+):\d+")[0].value_counts().to_string(header=False)
    )
    print("\n\nIn HPOA the reference column has (not unique values, simply counting):\n")
    print(raw_hpoa_counts, "\n")
    hpoa_unique = hpoa_df["reference"].unique()
    print(
        f"Within those, we have a set of {len(hpoa_unique)} unique lines, but some contain multiple references splitted by `;`.\n"
    )
    hpoa_set = set(hpoa_df["reference"].str.split(";").explode().dropna())
    print(
        f"Accounting for that, the set of actually unique PMID, ORPHAs and so on contains {len(hpoa_set)} items."
    )

    true_counts = (
        hpoa_df["reference"]
        .str.split(";")
        .explode()
        .dropna()
        .drop_duplicates()
        .str.extract(r"^([A-Z]+):\d+")[0]
        .value_counts()
    )

    print(f'After splitting multi-entries we obtain the following "distribution" of sources:\n')
    print(true_counts.to_string(header=False), "\n")
    no_correlation_ppkts = []

    def get_ref_ids_from_phenopacket(pkt_data):
        """Extract all ref IDs from externalReferences"""
        ref_ids = []
        external_refs = pkt_data.get("metaData", {}).get("externalReferences", [])
        for ref in external_refs:
            ref_id = ref.get("id", "")
            ref_ids.append(ref_id)
        return ref_ids

    phenopacket_origin_set = set()
    all_ppkt_refs = []

    for ppkt in phenopackets:
        ref_ids = get_ref_ids_from_phenopacket(ppkt)
        all_ppkt_refs.extend(ref_ids)
        phenopacket_origin_set.update(ref_ids)
        if any(refid not in hpoa_set for refid in ref_ids):
            no_correlation_ppkts.append(ppkt)

    print(f"We get {len(no_correlation_ppkts)} usable phenopackets.")

    # ppkt_raw_counts = pd.Series(all_ppkt_refs).str.extract(r"^([A-Z]+):\d+")[0].value_counts()
    # print(
    #     f"Phenopacket raw origin counts (counting duplicates):\n",
    #     ppkt_raw_counts.to_string(header=False),
    # )
    print(
        f"Phenopackets contain {len(phenopacket_origin_set)} unique reference IDs, and they are all PubMed IDs.\n"
    )

    # ppkt_true_counts = (
    #     pd.Series(list(phenopacket_origin_set))  # <-- convert set to list
    #     .str.extract(r"^([A-Z]+):\d+")[0]
    #     .value_counts()
    # )

    # print(f"Phenopacket unique counts per source:\n", ppkt_true_counts.to_string(header=False))
    intersection_size = len(hpoa_set & phenopacket_origin_set)
    print(f"Number of PubMed IDs in the intersection: {intersection_size}\n")
    print(
        f"Number of PubMed IDs in phenopacket-store \\ HPOA: {len(phenopacket_origin_set - hpoa_set)}\n"
    )
    print(
        f"Number of PubMed IDs in HPOA \\ phenopacket-store : {true_counts['PMID'] - intersection_size}\n"
    )

    filename = f"{output_config['file_prefix']}_hpoa{output_config['file_extension']}"
    file_path = os.path.join(output_dir, filename)
    with open(file_path, "w") as f:
        for pkt in no_correlation_ppkts:
            f.write(f"{pkt.get('_absolute_path', 'unknown')}\n")

    print(
        f"Written absolute paths to phenopacket JSON files that do not contain PubMed IDs also present in HPOA to this file: {file_path}"
    )
