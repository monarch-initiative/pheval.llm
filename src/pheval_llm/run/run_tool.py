from pathlib import Path

from pheval.utils.file_utils import all_files
from pheval.utils.phenopacket_utils import create_hgnc_dict

from malco.run.fake_predictor import predict_case


def run_tool(phenopacket_dir: Path, output_dir: Path) -> None:
    """
    Run the tool to obtain the raw results.

    Args:
        phenopacket_dir (Path): The path to the phenopacket directory.
        output_dir (Path): The path to the output directory.
    """
    hgnc_dict = create_hgnc_dict()
    gene_list = list(hgnc_dict.keys())
    seed = 0
    for phenopacket_path in all_files(phenopacket_dir):
        seed += 1
        predict_case(
            phenopacket_path=phenopacket_path, gene_list=gene_list, output_dir=output_dir, seed=seed
        )
