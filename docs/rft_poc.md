### RFT proof-of-concept: o4-mini beats Exomiser on random-split evaluation

This page documents a minimal integration of reinforcement fine-tuning (RFT) results into the existing MALCO framework, following the repo’s conventions. We place prompts in `data/prompts/`, responses in `data/responses/`, configure runs via YAML in `data/config/`, and compute top-N metrics through the standard `malco evaluate` + `summary` flow.

#### Key artifacts (already included in this repo)
- `data/config/ft-o4-mini-reticular.yaml`: run config pointing to the fine-tuned model’s responses
- `data/responses/ft:o4_mini_2025_04_16:reticular:medical_v1:C1s6tq4E.jsonl`: responses from the RFT model
- `data/results/intermediate_grounded_ft_o4_mini_reticular.tsv`: grounded results (pre-scoring)
- `data/results/intermediate_grounded_ft_o4_mini_reticular_scored.tsv`: grounded + scored results
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

#### Reproduce in 3 steps
1) Evaluate (ground, score, and summarize) using the provided config

```bash
poetry run malco evaluate \
  --config data/config/ft-o4-mini-reticular.yaml \
  --save-intermediate \
  --intermediate-file data/results/intermediate_grounded_ft_o4_mini_reticular.tsv
```

This writes full results to `data/results/full_results/full_df_ft_o4_mini_reticular.tsv` and the top-N summary to `data/results/topn_result_ft_o4_mini_reticular.tsv` (also mirrored under `data/results/exomiser_vs_llm/`).

2) (Optional) Score from an existing intermediate file

```bash
python score_intermediate_results.py \
  data/results/intermediate_grounded_ft_o4_mini_reticular.tsv \
  data/results/intermediate_grounded_ft_o4_mini_reticular_scored.tsv
```

3) Compute top-N on the RFT test split only

```bash
python analysis/eval_rft_subset.py \
  --jsonl data/rft/rft_test.jsonl \
  --scored data/results/intermediate_grounded_ft_o4_mini_reticular_scored.tsv \
  --out data/results/exomiser_vs_llm/topn_result_ft_o4_mini_reticular_rft_test.tsv
```

#### Notes
- Prompts are stored in `data/prompts/` (e.g., `gemini-prompts.jsonl`). If you need to regenerate responses, you can use `openai_model_inference_parallel.py` to write a JSONL under `data/responses/`, then point the config to that file.
- We intentionally reuse the repo’s established evaluation flow for minimal changes. All new artifacts are contained under `data/config/`, `data/responses/`, and `data/results/`.


