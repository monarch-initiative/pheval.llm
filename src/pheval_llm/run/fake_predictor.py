import json
import random
from pathlib import Path
from typing import List

from phenopackets import Phenopacket
from pheval.utils.phenopacket_utils import PhenopacketUtil, phenopacket_reader


class FakePredictor:
    """Class for predicting genes using a fake predictor."""

    def __init__(self, phenopacket: Phenopacket, gene_list: List[str]):
        """
        Initialise the FakePredictor class.

        Args:
            phenopacket (Phenopacket): The phenopacket object.
            gene_list (List[str]): The list of gene names.
        """
        self.phenopacket = phenopacket
        self.gene_list = gene_list
        self.random_generator = random.Random()

    def _get_known_genes(self) -> List[str]:
        """
        Get a list of known causative genes from the phenopacket.

        Returns:
            List[str]: The list of known causative genes.
        """
        diagnosed_genes = PhenopacketUtil(self.phenopacket).diagnosed_genes()
        return [diagnosed_gene.gene_symbol for diagnosed_gene in diagnosed_genes]

    def _get_random_list_of_predicted_genes(self) -> List[str]:
        """
        Get a list of 15 random genes from the gene list.

        Returns:
            List[str]: The list of 15 random genes.
        """
        return self.random_generator.choices(self.gene_list, k=15)

    def _get_list_of_predictions(self) -> List[str]:
        """
        Get a list of predicted genes containing both the known causative gene and randomly chosen genes.

        Returns:
            List[str]: The list of predicted genes.

        """
        return self._get_known_genes() + self._get_random_list_of_predicted_genes()

    def predict(self, seed) -> List[dict]:
        """
        Predict the causative genes for a phenopacket case.
        Args:
            seed (int): The random generator seed.
        Returns:
            List[dict]: A list of predictions.
        """
        self.random_generator.seed(seed)
        predictions = self._get_list_of_predictions()
        predictions_with_scores = []
        for prediction in predictions:
            predictions_with_scores.append(
                {"gene_symbol": prediction, "score": self.random_generator.uniform(0, 1)}
            )
        return predictions_with_scores


def predict_case(phenopacket_path: Path, gene_list: List[str], output_dir: Path, seed: int) -> None:
    """
    Predict genes for a phenopacket case.

    Args:
        phenopacket_path (Path): The path to the phenopacket.
        gene_list (List[str]): The list of all gene names.
        output_dir (Path): The path to the output directory to write the result.
        seed (int): The random generator seed.
    """
    phenopacket = phenopacket_reader(phenopacket_path)
    predictions = FakePredictor(phenopacket, gene_list).predict(seed)
    with open(output_dir.joinpath(phenopacket_path.name), "w") as output_file:
        json.dump(predictions, output_file, indent=4)
    output_file.close()
