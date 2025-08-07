#!/usr/bin/env python3
"""
Prepare data for reinforcement fine-tuning by splitting into train/test sets
and formatting in the required JSONL format.
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Tuple
import argparse


def load_exomiser_data(input_file: str) -> List[Dict]:
    """Load the exomiser gold standard data."""
    data = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def format_for_rft(data_item: Dict) -> Dict:
    """Format a single data item for RFT training.
    
    The RFT format requires:
    - messages: array of conversation messages
    - Additional fields for grading (gold_disease_name, gold_disease_id)
    """
    # Extract the prompt text
    prompt_text = data_item.get('prompt', '')
    
    # Extract gold standard data
    gold_data = data_item.get('gold', {})
    gold_disease_name = gold_data.get('disease_name', '')
    gold_disease_id = gold_data.get('disease_id', '')
    
    # Create the RFT format
    rft_item = {
        "messages": [
            {
                "role": "user",
                "content": prompt_text
            }
        ],
        "gold_disease_name": gold_disease_name,
        "gold_disease_id": gold_disease_id,
        "case_id": data_item.get('id', 'unknown')
    }
    
    return rft_item


def split_and_save_data(
    data: List[Dict],
    output_dir: str,
    train_ratio: float = 0.7,
    valid_ratio: float = 0.1,
    test_ratio: float = 0.2,
    seed: int = 42
) -> Tuple[str, str, str]:
    """Split data into train/valid/test sets and save as JSONL files."""
    # Validate ratios
    total_ratio = train_ratio + valid_ratio + test_ratio
    if abs(total_ratio - 1.0) > 0.001:
        raise ValueError(f"Train + valid + test ratios must equal 1.0, got {total_ratio}")
    
    # Set random seed for reproducibility
    random.seed(seed)
    
    # Shuffle data
    shuffled_data = data.copy()
    random.shuffle(shuffled_data)
    
    # Calculate split points
    train_size = int(len(shuffled_data) * train_ratio)
    valid_size = int(len(shuffled_data) * valid_ratio)
    
    # Split data
    train_data = shuffled_data[:train_size]
    valid_data = shuffled_data[train_size:train_size + valid_size]
    test_data = shuffled_data[train_size + valid_size:]
    
    # Format data for RFT
    train_formatted = [format_for_rft(item) for item in train_data]
    valid_formatted = [format_for_rft(item) for item in valid_data]
    test_formatted = [format_for_rft(item) for item in test_data]
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save files
    train_file = output_path / "rft_train.jsonl"
    valid_file = output_path / "rft_valid.jsonl"
    test_file = output_path / "rft_test.jsonl"
    
    # Write train file
    with open(train_file, 'w', encoding='utf-8') as f:
        for item in train_formatted:
            json.dump(item, f, ensure_ascii=False)
            f.write('\n')
    
    # Write validation file
    with open(valid_file, 'w', encoding='utf-8') as f:
        for item in valid_formatted:
            json.dump(item, f, ensure_ascii=False)
            f.write('\n')
    
    # Write test file
    with open(test_file, 'w', encoding='utf-8') as f:
        for item in test_formatted:
            json.dump(item, f, ensure_ascii=False)
            f.write('\n')
    
    print(f"Dataset split complete:")
    print(f"  Total samples: {len(data)}")
    print(f"  Training samples: {len(train_data)} ({train_ratio*100:.0f}%)")
    print(f"  Validation samples: {len(valid_data)} ({valid_ratio*100:.0f}%)")
    print(f"  Test samples: {len(test_data)} ({test_ratio*100:.0f}%)")
    print(f"  Training data saved to: {train_file}")
    print(f"  Validation data saved to: {valid_file}")
    print(f"  Test data saved to: {test_file}")
    
    # Also save a metadata file with statistics
    metadata = {
        "total_samples": len(data),
        "train_samples": len(train_data),
        "valid_samples": len(valid_data),
        "test_samples": len(test_data),
        "train_ratio": train_ratio,
        "valid_ratio": valid_ratio,
        "test_ratio": test_ratio,
        "seed": seed,
        "unique_diseases": len(set(item.get('gold', {}).get('disease_name', '') for item in data))
    }
    
    metadata_file = output_path / "rft_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    return str(train_file), str(valid_file), str(test_file)


def main():
    parser = argparse.ArgumentParser(
        description="Prepare data for reinforcement fine-tuning"
    )
    parser.add_argument(
        "--input-file",
        type=str,
        default="data/exomiser-gold.jsonl",
        help="Input JSONL file with exomiser gold standard data"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/rft",
        help="Output directory for RFT-formatted data"
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.7,
        help="Ratio of data to use for training (default: 0.7)"
    )
    parser.add_argument(
        "--valid-ratio",
        type=float,
        default=0.1,
        help="Ratio of data to use for validation (default: 0.1)"
    )
    parser.add_argument(
        "--test-ratio",
        type=float,
        default=0.2,
        help="Ratio of data to use for testing (default: 0.2)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    
    args = parser.parse_args()
    
    # Load data
    print(f"Loading data from: {args.input_file}")
    data = load_exomiser_data(args.input_file)
    
    if not data:
        print("No data found!")
        return
    
    # Split and save
    split_and_save_data(
        data,
        args.output_dir,
        args.train_ratio,
        args.valid_ratio,
        args.test_ratio,
        args.seed
    )


if __name__ == "__main__":
    main()