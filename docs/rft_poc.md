### RFT proof-of-concept: o4-mini with Reinforcement Fine-Tuning (RFT) beats Exomiser on random-split evaluation

This page documents a minimal integration of reinforcement fine-tuning (RFT) results into the existing MALCO framework, following the repo’s conventions.

#### Headline results

| Model / Run                                                                 | Top-1                | Top-10               | Not ranked (`nf`)      |
|----------------------------------------------------------------------------|----------------------|----------------------|------------------------|
| Exomiser baseline (aggregated)                                             | 1,852 (35.5%)        | 3,047 (58.4%)        | 2,165 (41.5%)          |
| o1-preview ([topn_result_o1_preview.tsv](data/results/exomiser_vs_llm/topn_result_o1_preview.tsv)) | 1,232 (23.6%)        | 1,693 (32.5%)        | 3,293 (63.1%)          |
| o4-mini (no RFT, [topn_result_o4_mini.tsv](data/results/exomiser_vs_llm/topn_result_o4_mini.tsv)) | 1,210 (23.2%)        | 1,893 (36.3%)        | 3,278 (62.7%)          |
| o4-mini RFT (trained on random 70% split, run `ft`, 5,212 cases)           | 2,313 (44.4%)        | 2,978 (57.1%)        | 2,235 (42.9%)          |
| o4-mini RFT test split (20% heldout, run `ft_rft_test`, 1,043 cases)       | 430 (41.2%)          | 591 (56.6%)          | 452 (43.3%)            |

These demonstrate a proof-of-concept where the RFT model’s Top-1 on the full dataset exceeds the Exomiser baseline’s Top-1 count, and it achieves strong performance on the held-out RFT test split.

#### Model Responses
We place prompts in `data/prompts/`, responses in `data/responses/`, configure runs via YAML in `data/config/`, and compute top-N metrics through the standard `malco evaluate` + `summary` flow.

#### Key artifacts (already included in this repo)
- `data/config/ft-o4-mini-reticular.yaml`: run config pointing to the fine-tuned model’s responses
- `data/responses/ft-o4-mini-reticular.jsonl`: responses from the RFT model
- `data/results/full_results/ft_o4_mini_reticular_scored.tsv`: grounded + scored results table
- `data/results/exomiser_vs_llm/topn_result_ft_o4_mini_reticular.tsv`: top-N for full dataset using the RFT model (run = `ft`)
- `data/results/exomiser_vs_llm/topn_result_ft_o4_mini_reticular_rft_test.tsv`: top-N for the RFT test split (run = `ft_rft_test`)
- `data/results/exomiser_vs_llm/topn_result_Exomiser.tsv`: Exomiser baseline top-N


#### Reproduce
1) Evaluate (ground, score, and summarize) using the provided config

```bash
poetry run malco evaluate \
  --config data/config/ft-o4-mini-reticular.yaml \
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

- **Data split:** We used a random split of the dataset: 70% for training, 10% for validation, and 20% for testing. Because there are a limited number of unique diseases, this random split may favor deep learning approaches like RFT. In this PR, we just quickly tested this to generate a proof-of-concept. For more robust benchmarking, heldout disease splits could be considered.
- **Structured outputs:** For o4 models, outputs were enforced to be structured as numbered diagnosis lists to reduce model refusal rate. This enforcement did not materially change baseline performance; the o4-mini (no RFT) run performed similarly to o1 in our tests.
- Prompts are stored in `data/prompts/` (e.g., `gemini-prompts.jsonl`). If you need to regenerate responses, use `notebooks/o4_and_rft/o4_inference.py` to write a JSONL under `data/responses/`, then ensure the config points to that file.
- We intentionally reuse the repo’s established evaluation flow for minimal changes. All new artifacts are contained under `data/config/`, `data/responses/`, and `data/results/`.