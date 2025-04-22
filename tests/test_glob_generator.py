import unittest

from malco.model.language import Language
from malco.process.generate_plots import glob_generator


class TestGlobGenerator(unittest.TestCase):

    def test_glob_generator(self):
        input = (("GPT_4o", [Language.EN]), ("*", [Language.IT]), ("*", [Language.ALL]), ("GPT_4o", [Language.IT, Language.ES]))
        expected = ("topn_result_GPT_4o.tsv", "topn_result_it-*.tsv", "topn_result_*_*.tsv", 'topn_result_{it,es}_GPT_4o_*.tsv')
        for inputs, ex in zip(input, expected):
            glob = glob_generator(inputs[0], inputs[1])
            self.assertEqual(glob, ex)
