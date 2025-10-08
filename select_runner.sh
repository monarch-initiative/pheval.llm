#!/usr/bin/env bash

# Ensure script is run with bash
if [ -z "$BASH_VERSION" ]; then
  echo "This script must be run with bash, not sh or dash." >&2
  exit 1
fi

# Usage: ./select_runner.sh -a <analysis_type> -m <model1,model2,...|all>
# Example: ./select_runner.sh -a nHPO -m all

# Hardcoded model names
MODEL_NAMES=(exomiser14 geminiflash gpt-01-mini gpt-01-preview gpt-4o medfound176b meditron2-70b meditron3-70b)

# Function to map model name to display label
model_label() {
  case "$1" in
    exomiser14) echo "Exomiser 14" ;;
    geminiflash) echo "GeminiFlash" ;;
    gpt-01-mini) echo "GPT-0.1 Mini" ;;
    gpt-01-preview) echo "GPT-0.1 Preview" ;;
    gpt-4o) echo "GPT-4o" ;;
    medfound176b) echo "MedFound 176B" ;;
    meditron2-70b) echo "Meditron2 70B" ;;
    meditron3-70b) echo "Meditron3 70B" ;;
    *) echo "$1" ;;
  esac
}

while getopts "a:m:" opt; do
  case $opt in
    a) analysis_type="$OPTARG" ;;
    m) models_arg="$OPTARG" ;;
    \?) echo "Invalid option -$OPTARG" >&2; exit 1 ;;
  esac
done

if [[ -z "$analysis_type" || -z "$models_arg" ]]; then
  echo "Usage: $0 -a <analysis_type> -m <model1,model2,...|all>"
  exit 1
fi

if [[ "$models_arg" == "all" ]]; then
  models=("${MODEL_NAMES[@]}")
else
  IFS=',' read -ra models <<< "$models_arg"
fi

echo
for model in "${models[@]}"; do
  echo "Running analysis for model: $(model_label "$model") ($model), type: $analysis_type"
  case "$analysis_type" in
    nHPO_1_5|nHPO_6_10|nHPO_11_20|nHPO_21_50)
        range="${analysis_type#nHPO_}"
        cases_file="analysis_out/phenopacket_subsets/nHPO/phenopackets_${range//_/-}.txt"
        altpath="data/results/ex_vs_llm_review/${analysis_type}/topn_result_${range}_HPO_${model}.tsv"
        poetry run malco select \
        --config "data/config/ex_vs_llm_review/${model}.yaml" \
        --cases "$cases_file" \
        --altpath "$altpath"
        ;;
    rare|common)
        prevalence="${analysis_type#prevalence_}"
        cases_file="analysis_out/phenopacket_subsets/prevalence/phenopackets_${analysis_type}.txt"
        altpath="data/results/ex_vs_llm_review/${analysis_type}/topn_result_${analysis_type}_${model}.tsv"
        poetry run malco select \
            --config "data/config/ex_vs_llm_review/${model}.yaml" \
            --cases "$cases_file" \
            --altpath "$altpath"
      ;;
    cardiovascular|immunological|neurological)
        cases_file="analysis_out/phenopacket_subsets/disease_category/phenopackets_${analysis_type}.txt"
        altpath="data/results/ex_vs_llm_review/${analysis_type}/topn_result_${analysis_type}_${model}.tsv"
        poetry run malco select \
        --config "data/config/ex_vs_llm_review/${model}.yaml" \
        --cases "$cases_file" \
        --altpath "$altpath"
        ;;
    *)
      echo "Unknown analysis type: $analysis_type" >&2
      exit 1
      ;;
  esac
done