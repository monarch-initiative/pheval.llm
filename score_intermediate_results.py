#!/usr/bin/env python3
"""
Script to load intermediate grounded results and run the scoring process.
This is useful when you have intermediate results saved and want to score them separately.

Usage:
    # Use default intermediate file
    python score_intermediate_results.py
    
    # Specify intermediate file (output will be auto-generated)
    python score_intermediate_results.py path/to/intermediate.tsv
    
    # Specify both input and output files
    python score_intermediate_results.py path/to/intermediate.tsv path/to/output.tsv
    
The script handles common errors gracefully and provides detailed progress information.
"""

import sys
import os
import pandas as pd
import ast
from pathlib import Path

# Add src to path so we can import malco
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from malco.process.scoring import score, mondo_adapter
    from malco.config.malco_config import MalcoConfig
    
    def load_and_score_intermediate(intermediate_file_path, output_file_path=None):
        """
        Load intermediate grounded results and score them.
        
        Args:
            intermediate_file_path: Path to the intermediate TSV file
            output_file_path: Optional path to save the scored results
        """
        print(f"Loading intermediate results from: {intermediate_file_path}")
        
        # Load the intermediate dataframe
        df = pd.read_csv(intermediate_file_path, sep='\t')
        print(f"Loaded {len(df)} rows")
        print(f"Columns: {list(df.columns)}")
        
        # Fix column naming - scoring function expects 'id' but intermediate has 'metadata'
        if 'metadata' in df.columns and 'id' not in df.columns:
            df = df.rename(columns={'metadata': 'id'})
            print("Renamed 'metadata' column to 'id' for scoring compatibility")
        
        # Parse the grounding and gold columns (they're stored as strings)
        print("Parsing grounding and gold columns...")
        
        rows_with_errors = []
        
        for index, row in df.iterrows():
            try:
                # Parse the grounding column
                if pd.notna(row['grounding']) and row['grounding'] != '':
                    df.at[index, 'grounding'] = ast.literal_eval(row['grounding'])
                else:
                    df.at[index, 'grounding'] = []
                
                # Parse the gold column
                if pd.notna(row['gold']) and row['gold'] != '':
                    df.at[index, 'gold'] = ast.literal_eval(row['gold'])
                else:
                    df.at[index, 'gold'] = {}
                    
            except (ValueError, SyntaxError) as e:
                rows_with_errors.append((index, str(e)))
                print(f"Warning: Error parsing row {index}: {e}")
                # Set default values for problematic rows
                df.at[index, 'grounding'] = []
                df.at[index, 'gold'] = {}
        
        if rows_with_errors:
            print(f"Found {len(rows_with_errors)} rows with parsing errors. These will be skipped during scoring.")
            print("First few errors:")
            for i, (idx, error) in enumerate(rows_with_errors[:5]):
                print(f"  Row {idx}: {error}")
        
        # Initialize mondo adapter
        print("Initializing Mondo adapter...")
        mondo_adapter()
        
        # Score the results
        print("Starting scoring process...")
        try:
            df_scored = score(df)
            print("Scoring completed successfully!")
            
            # Save the results if output path is provided
            if output_file_path:
                # Remove service_answers column to save space (like in the original code)
                df_output = df_scored.drop("service_answers", axis=1) if "service_answers" in df_scored.columns else df_scored
                df_output.to_csv(output_file_path, sep="\t", index=False)
                print(f"Scored results saved to: {output_file_path}")
            
            return df_scored
            
        except Exception as e:
            print(f"Error during scoring: {e}")
            print("This might be due to missing dependencies or configuration issues.")
            raise
    
    if __name__ == "__main__":
        # Allow command line arguments
        if len(sys.argv) > 1:
            intermediate_file = sys.argv[1]
            # Auto-generate output filename based on input
            base_name = os.path.splitext(intermediate_file)[0]
            output_file = f"{base_name}_scored.tsv"
        else:
            # Default paths
            intermediate_file = "data/results/intermediate_grounded_o4_mini.tsv"
            output_file = "data/results/scored_from_intermediate_o4_mini.tsv"
            
        if len(sys.argv) > 2:
            output_file = sys.argv[2]
        
        print("=" * 60)
        print("MALCO Intermediate Results Scorer")
        print("=" * 60)
        print(f"Input file: {intermediate_file}")
        print(f"Output file: {output_file}")
        print("=" * 60)
        
        # Check if input file exists
        if not os.path.exists(intermediate_file):
            print(f"Error: Input file does not exist: {intermediate_file}")
            sys.exit(1)
        
        try:
            # Load and score
            df_scored = load_and_score_intermediate(intermediate_file, output_file)
            
            print("\n" + "=" * 60)
            print("SCORING SUMMARY")
            print("=" * 60)
            print(f"Total rows processed: {len(df_scored)}")
            print(f"Columns in final result: {list(df_scored.columns)}")
            
            # Show some basic stats if scored column exists
            if 'scored' in df_scored.columns:
                non_empty_scored = df_scored['scored'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False).sum()
                print(f"Rows with scoring results: {non_empty_scored}")
            
            print("=" * 60)
            print("SUCCESS: Scoring completed!")
            
        except KeyboardInterrupt:
            print("\nProcess interrupted by user.")
            sys.exit(1)
        except Exception as e:
            print(f"\nFATAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're in the correct environment and all dependencies are installed.")
    print("Try: source .venv/bin/activate")
    sys.exit(1)