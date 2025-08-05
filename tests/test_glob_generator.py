import unittest
from pathlib import Path
from unittest.mock import MagicMock
from malco.model.language import Language
from malco.process.generate_plots import glob_generator


class TestGlobGenerator(unittest.TestCase):

    def test_glob_generator(self):
        """Test just the pattern generation logic without files"""
        inputs = (
            ("GPT_4o", [Language.EN]),
            ("*", [Language.IT]),
            ("*", [Language.ALL]),
            ("GPT_4o", [Language.IT, Language.ES]),
        )
        expected = (
            "topn_result_GPT_4o.tsv",
            "topn_result_it-*.tsv",
            "topn_result_*-*.tsv",
            "topn_result_{it,es}_GPT_4o_*.tsv",
        )

        # Mock the Path.glob method to return the pattern we're sending
        for input, ex in zip(inputs, expected):
            with self.subTest(input=input):
                # Create a mock Path object
                mock_dir = MagicMock(spec=Path)

                # Call the function with mock directory
                glob_generator(input[0], input[1], mock_dir)

                # Check if glob was called with the expected pattern
                mock_dir.glob.assert_called_once_with(ex)
