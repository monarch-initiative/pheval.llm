Before starting a run take care of editing the [yaml](data/config/) as follows:

- The first line contains a non-empty comma-separated list of (supported) language codes between double quotation marks in which one wishes to prompt.
- The second line contains a non-empty comma-separated list of (supported) model names between double quotation marks which one wishes to prompt.
- The third line contains two comma-separated binary entries, represented by 0 (false) and 1 (true). The first set to true runs the prompting and grounding, i.e. the run step, the second one executes the scoring and the rest of the analysis, i.e. the post processing step. 

At this point one can install and run the code by doing:
```shell
poetry install
poetry env activate
#TODO
```

As an example, the [input file](https://github.com/monarch-initiative/pheval.llm/tree/main/docs/run_parameters.csv) file will execute only the post_process block for English, prompting the models gpt-4, gpt-3.5-turbo, gpt-4o, and gpt-4-turbo.
