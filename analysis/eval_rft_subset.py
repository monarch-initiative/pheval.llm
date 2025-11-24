#!/usr/bin/env python3
"""
Subset finetuned model scored results to RFT test cases and compute top-N metrics.

Inputs (defaults are correct for this repo):
  - --jsonl: data/rft/rft_test.jsonl
  - --scored: data/results/intermediate_grounded_ft_o4_mini_reticular_scored.tsv
  - --out: data/results/topn_result_ft_o4_mini_reticular_rft_test.tsv

Output:
  - A topn_result TSV with the same header as other runs
  - Printed top-1/top-5/top-10 accuracies
"""

from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from pathlib import Path
from typing import Iterable, List, Dict, Any

import pandas as pd


def read_case_ids(jsonl_path: Path) -> List[str]:
    case_ids: List[str] = []
    with jsonl_path.open("r") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            cid = obj.get("case_id")
            if cid:
                case_ids.append(cid)
    return case_ids


def parse_scored_column(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure 'scored' column is a list[dict]
    parsed: List[List[Dict[str, Any]]] = []
    for val in df["scored"].tolist():
        if isinstance(val, list):
            parsed.append(val)
            continue
        if pd.isna(val) or val == "" or val is None:
            parsed.append([])
            continue
        try:
            parsed.append(ast.literal_eval(val))
        except Exception:
            parsed.append([])
    df = df.copy()
    df["scored"] = parsed
    return df


def summarize_topn(rows: Iterable[Dict[str, Any]]) -> Counter:
    """Replicate logic from malco.process.summary.summarize for consistency."""
    rank_counter: Counter = Counter()
    for row in rows:
        scored = row.get("scored") or []
        correct_rank = None
        grounding_failure = None
        item_number = None

        if len(scored) > 0:
            rank_counter["nc"] += 1  # case processed
            sdf = pd.DataFrame(scored)
            correct_rank = (
                sdf.index[sdf["is_correct"] == True].min() + 1  # noqa: E712
                if not sdf[sdf["is_correct"] == True].empty  # noqa: E712
                else None
            )
            grounding_failure = any(sdf["grounded_id"] == "N/A")
            item_number = len(sdf)

        if correct_rank is not None and 1 <= correct_rank <= 10:
            rank_counter[f"n{correct_rank}"] += 1
        elif correct_rank is not None and correct_rank > 10:
            rank_counter["n10p"] += 1
        else:
            rank_counter["nf"] += 1

        if grounding_failure is True:
            rank_counter["tgf"] += 1
            if correct_rank is None:
                rank_counter["gf"] += 1

        if item_number is not None:
            rank_counter["items"] += item_number

    return rank_counter


def write_topn_tsv(out_path: Path, run_name: str, c: Counter, num_cases: int) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "run\tn1\tn2\tn3\tn4\tn5\tn6\tn7\tn8\tn9\tn10\tn10p\tnf\tgrounding_failed\t"
        "num_cases\ttotal_grounding_failures\titems_processed\n"
    )
    row = [
        run_name,
        c.get("n1", 0),
        c.get("n2", 0),
        c.get("n3", 0),
        c.get("n4", 0),
        c.get("n5", 0),
        c.get("n6", 0),
        c.get("n7", 0),
        c.get("n8", 0),
        c.get("n9", 0),
        c.get("n10", 0),
        c.get("n10p", 0),
        c.get("nf", 0),
        c.get("gf", 0),
        num_cases,
        c.get("tgf", 0),
        c.get("items", 0),
    ]
    with out_path.open("w") as f:
        f.write(header)
        f.write("\t".join(map(str, row)) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--jsonl",
        default="data/rft/rft_test.jsonl",
        type=str,
        help="RFT test JSONL with case_id field",
    )
    ap.add_argument(
        "--scored",
        default="data/results/intermediate_grounded_ft_o4_mini_reticular_scored.tsv",
        type=str,
        help="Scored TSV with columns id, scored",
    )
    ap.add_argument(
        "--out",
        default="data/results/topn_result_ft_o4_mini_reticular_rft_test.tsv",
        type=str,
        help="Output topn_result TSV path",
    )
    ap.add_argument(
        "--run_name",
        default="ft_rft_test",
        type=str,
        help="Run name to write in the topn TSV",
    )
    args = ap.parse_args()

    jsonl_path = Path(args.jsonl)
    scored_path = Path(args.scored)
    out_path = Path(args.out)

    case_ids = read_case_ids(jsonl_path)
    if len(case_ids) == 0:
        raise SystemExit("No case_id values found in JSONL")

    df = pd.read_csv(scored_path, sep="\t", usecols=["id", "scored"], dtype={"id": str})
    df = parse_scored_column(df)

    subset = df[df["id"].isin(set(case_ids))].copy()
    num_cases = len(subset)
    if num_cases == 0:
        raise SystemExit("No matching cases between JSONL case_id and scored TSV 'id'.")

    counter = summarize_topn(subset.to_dict(orient="records"))

    write_topn_tsv(out_path, args.run_name, counter, num_cases)

    n1 = counter.get("n1", 0)
    n5 = sum(counter.get(f"n{i}", 0) for i in range(1, 6))
    n10 = sum(counter.get(f"n{i}", 0) for i in range(1, 11))

    print(f"Subset size: {num_cases}")
    print(f"Top-1: {n1}/{num_cases} = {n1/num_cases:.2%}")
    print(f"Top-5: {n5}/{num_cases} = {n5/num_cases:.2%}")
    print(f"Top-10: {n10}/{num_cases} = {n10/num_cases:.2%}")
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()


