import unittest

from malco.post_process.mondo_score_utils import omim_mappings
from malco.post_process.ranking_utils import get_adapter


class TestOntologyUtils(unittest.TestCase):

    def test_mappings(self):
        mondo_input = "MONDO:0007566"
        omims_output = omim_mappings(mondo_input, get_adapter("sqlite:obo:mondo"))
        truth = ["OMIM:132800"]
        self.assertEqual(truth, omims_output)
