# pheval.llm 

![Contributors](https://img.shields.io/github/contributors/monarch-initiative/pheval.llm?style=plastic)
![Stars](https://img.shields.io/github/stars/monarch-initiative/pheval.llm)
![Licence](https://img.shields.io/github/license/monarch-initiative/pheval.llm)
![Issues](https://img.shields.io/github/issues/monarch-initiative/pheval.llm)

## Evaluate LLMs' capability at performing differential diagnosis for rare genetic diseases through medical-vignette-like prompts created with [phenopacket2prompt](https://github.com/monarch-initiative/phenopacket2prompt). 

### Description
To systematically assess and evaluate an LLM's ability to perform differential diagnostics tasks, we employed prompts programatically created with [phenopacket2prompt](https://github.com/monarch-initiative/phenopacket2prompt), thereby avoiding any patient privacy issues. The original data are phenopackets located at [phenopacket-store](https://github.com/monarch-initiative/phenopacket-store/). A programmatic approach for scoring and grounding results is also developed, made possible thanks to the ontological structure of the [Mondo Disease Ontology](https://mondo.monarchinitiative.org/).

Two main analyses are carried out:
- A benchmark of some openAI GPT-models against a state of the art tool for differential diagnostics, [Exomiser](https://github.com/exomiser/Exomiser). The bottom line, Exomiser [clearly outperforms the LLMs](https://github.com/monarch-initiative/pheval.llm/blob/short_letter/notebooks/plot_exomiser_o1MINI_o1PREVIEW_4o.ipynb).
- A comparison of gpt-4o's ability to carry out differential diagnosis when prompted in different languages. 

Formerly MALCO, Multilingual Analysis of LLMs for Clinical Observations.
Built using the [PhEval](https://github.com/monarch-initiative/pheval) runner template.


# Usage
Before starting a run take care of editing the [run parameters](inputdir/run_parameters.csv) as follows:
- The first line contains a non-empty comma-separated list of (supported) language codes between double quotation marks in which one wishes to prompt.
- The second line contains a non-empty comma-separated list of (supported) model names between double quotation marks which one wishes to prompt.
- The third line contains two comma-separated binary entries, represented by 0 (false) and 1 (true). The first set to true runs the prompting and grounding, i.e. the run step, the second one executes the scoring and the rest of the analysis, i.e. the post processing step. 

At this point one can install and run the code by doing
```shell
poetry install
poetry shell
mkdir outputdirectory
cp -r /path/to/promptdir inputdir/
pheval run -i inputdir -r "malcorunner" -o outputdirectory -t tests
```

