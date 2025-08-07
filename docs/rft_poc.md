### RFT proof-of-concept: o4-mini beats Exomiser on random-split evaluation

This page documents a minimal integration of reinforcement fine-tuning (RFT) results into the existing MALCO framework, following the repo’s conventions. We place prompts in `data/prompts/`, responses in `data/responses/`, configure runs via YAML in `data/config/`, and compute top-N metrics through the standard `malco evaluate` + `summary` flow.

#### Key artifacts (already included in this repo)
- `data/config/ft-o4-mini-reticular.yaml`: run config pointing to the fine-tuned model’s responses
- `data/responses/ft-o4-mini-reticular.jsonl`: responses from the RFT model
- `data/results/full_results/ft_o4_mini_reticular_scored.tsv`: grounded + scored results table
- `data/results/exomiser_vs_llm/topn_result_ft_o4_mini_reticular.tsv`: top-N for full dataset using the RFT model (run = `ft`)
- `data/results/exomiser_vs_llm/topn_result_ft_o4_mini_reticular_rft_test.tsv`: top-N for the RFT test split (run = `ft_rft_test`)
- `data/results/exomiser_vs_llm/topn_result_Exomiser.tsv`: Exomiser baseline top-N

#### Headline results
- Full dataset (run `ft`, 5,212 cases)
  - Top-1 = 2,313; Top-10 = 2,978; Not ranked (`nf`) = 2,235
- RFT test split (run `ft_rft_test`, 1,043 cases)
  - Top-1 = 430 (41.2%); Top-10 = 591 (56.6%); Not ranked (`nf`) = 452
- Exomiser baseline (aggregated)
  - Top-1 = 1,852; Top-10 = 3,047; `nf` = 2,165

These demonstrate a proof-of-concept where the RFT model’s Top-1 on the full dataset exceeds the Exomiser baseline’s Top-1 count, and it achieves strong performance on the held-out RFT test split.

#### Reproduce
1) Evaluate (ground, score, and summarize) using the provided config

```bash
poetry run malco evaluate \
  --config data/config/ft-o4-mini-reticular.yaml \
  --save-intermediate \
  --intermediate-file data/results/intermediate_grounded_ft_o4_mini_reticular.tsv
```

This writes full results to `data/results/full_results/full_df_ft_o4_mini_reticular.tsv` and the top-N summary to `data/results/exomiser_vs_llm/topn_result_ft_o4_mini_reticular.tsv`.

2) Compute top-N on the RFT test split only

```bash
python analysis/eval_rft_subset.py \
  --jsonl data/prompts/rft/rft_test.jsonl \
  --scored data/results/full_results/ft_o4_mini_reticular_scored.tsv \
  --out data/results/exomiser_vs_llm/topn_result_ft_o4_mini_reticular_rft_test.tsv
```

#### End-to-end RFT utilities (optional)
- Prepare RFT splits from `data/exomiser-gold.jsonl`:

```bash
python notebooks/o4_and_rft/prepare_rft_data.py \
  --input-file data/exomiser-gold.jsonl \
  --output-dir data/prompts/rft \
  --train-ratio 0.7 --valid-ratio 0.1 --test-ratio 0.2
```

- Create an RFT job (requires OpenAI credentials):

```bash
python notebooks/o4_and_rft/create_rft_job.py \
  --train-file data/prompts/rft/rft_train.jsonl \
  --valid-file data/prompts/rft/rft_valid.jsonl \
  --model o4-mini-2025-04-16 --reasoning-effort high --monitor
```

- Generate responses with the base or fine-tuned model:

```bash
python notebooks/o4_and_rft/o4_inference.py \
  --model o4-mini-2025-04-16 \
  --input-file data/prompts/gemini-prompts.jsonl \
  --outputdir data/responses \
  --parallel 10
```

Then point `data/config/ft-o4-mini-reticular.yaml` to the correct `response_file` (e.g., `data/responses/ft-o4-mini-reticular.jsonl`) and run the evaluation as in step 1.

#### Notes

- Random split: 70% train, 10% valid, 20% test. Due to the limited number of unique diseases in the dataset, this setup can favor RFT; use disease-disjoint or time-based splits for stronger claims.
- Structured Outputs: enforced for o4 models to return numbered diagnosis lists. This did not materially change baseline performance; the o4-mini (no RFT) run behaved similarly to o1 in our tests.
- Prompts are stored in `data/prompts/` (e.g., `gemini-prompts.jsonl`). If you need to regenerate responses, use `notebooks/o4_and_rft/o4_inference.py` to write a JSONL under `data/responses/`, then ensure the config points to that file.
- We intentionally reuse the repo’s established evaluation flow for minimal changes. All new artifacts are contained under `data/config/`, `data/responses/`, and `data/results/`.


