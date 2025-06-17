# MALCO

![Contributors](https://img.shields.io/github/contributors/monarch-initiative/pheval.llm?style=plastic)
![Stars](https://img.shields.io/github/stars/monarch-initiative/pheval.llm)
![Licence](https://img.shields.io/github/license/monarch-initiative/pheval.llm)
![Issues](https://img.shields.io/github/issues/monarch-initiative/pheval.llm)

## Evaluate LLMs' capability at performing differential diagnosis for rare genetic diseases through medical-vignette-like prompts created with [phenopacket2prompt](https://github.com/monarch-initiative/phenopacket2prompt). 

### Description
To systematically assess and evaluate an LLM's ability to perform differential diagnostics tasks, we employed prompts programatically created with [phenopacket2prompt](https://github.com/monarch-initiative/phenopacket2prompt), thereby avoiding any patient privacy issues. The original data are phenopackets located at [phenopacket-store](https://github.com/monarch-initiative/phenopacket-store/). A programmatic approach for scoring and grounding results is also developed, made possible thanks to the ontological structure of the [Mondo Disease Ontology](https://mondo.monarchinitiative.org/).

Two main analyses are carried out:
- A benchmark of some large language models against the state of the art tool for differential diagnostics, [Exomiser](https://github.com/exomiser/Exomiser). The bottom line, Exomiser clearly outperforms the LLMs as per our [preprint](https://www.medrxiv.org/content/10.1101/2024.07.22.24310816v3), [data at this zenodo](https://doi.org/10.5281/zenodo.14008476).
- A comparison of gpt-4o's and [Meditron3-70B](https://huggingface.co/OpenMeditron/Meditron3-70B) ability to carry out differential diagnosis when prompted in 10 different languages, results at this [medRxiv](https://www.medrxiv.org/content/10.1101/2025.02.26.25322769v1) or [zenodo](https://doi.org/10.5281/zenodo.14804250) (see also this related [link](https://doi.org/10.5281/zenodo.15065293) for some more data). 

# Setup
## Dependencies
```
    poetry install
```
> **Note:** If you are unfamiliar with poetry, just `pip install .` and then activate the environment, omitting `poetry run` from the following instructions.

## Configure CurateGPT
```
    export OPENAI_API_KEY=<your key>
    poetry run curategpt ontology index --index-fields label,definition,relationships -p stagedb -c ont_mondo -m openai: sqlite:obo:mondo
```
Where the embedding model is selected via the `-m` argument. For non openAI models, we refer to the CurateGPT [documentation](https://github.com/monarch-initiative/curategpt?tab=readme-ov-file#selecting-models).
# Usage

## Grounding & Scoring Single Response
```
    cp data/config/default.yaml data/config/<your_model>.yaml
    poetry run malco evaluate --config data/config/meditron3-70b.yaml
```
## Plotting Single Model Results
```
    poetry run malco plot --config data/config/meditron3-70b.yaml 
```
## Plotting Single Model By All Languages Results
```
    poetry run malco combine --dir data/results --lang ALL
```
## Plotting Multiple Model Results
```
    poetry run malco combine --dir data/results
```
