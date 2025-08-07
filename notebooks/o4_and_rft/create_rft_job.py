#!/usr/bin/env python3
"""
Create a reinforcement fine-tuning job for o4-mini with a fuzzy string match grader.
"""

import os
import json
import argparse
import time
import requests  # Add this import
from typing import Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pathlib import Path

# Load environment variables
load_dotenv()


class DiagnosisItem(BaseModel):
    """Individual diagnosis item for structured output"""
    rank: int = Field(..., description="Rank of the diagnosis (1 = most likely)")
    disease_name: str = Field(..., description="Name of the disease")


class DiagnosisResponse(BaseModel):
    """Structured response for differential diagnosis"""
    diagnoses: list[DiagnosisItem] = Field(
        ..., 
        description="List of candidate diagnoses ranked by probability",
        min_items=1
    )


def create_fuzzy_match_grader() -> Dict:
    """Create a text similarity grader using fuzzy string matching.

    This grader checks how similar the model's output is to the true disease name
    using a fuzzy string match metric.
    """
    grader_config = {
        "type": "text_similarity",
        "name": "Fuzzy Disease Name Match",
        "input": "{{sample.output_text}}",
        "reference": "{{item.gold_disease_name}}",
        "pass_threshold": 0.5,  # 80% similarity threshold
        "evaluation_metric": "fuzzy_match"
    }
    return grader_config


def create_structured_output_grader() -> Dict:
    """Create a multi-grader for structured output that checks the diagnoses list."""
    grader_config = {
        "type": "multi",
        "graders": {
            "disease_match": {
                "type": "score_model",
                "name": "Disease Match Score",
                "model": "gpt-4o-2024-08-06",
                "input": [
                    {
                        "role": "system",
                        "content": "You are an expert medical grader. Score how well the model's diagnoses match the reference disease."
                    },
                    {
                        "role": "user",
                        "content": """Reference disease: {{item.gold_disease_name}}
                        
Model's diagnoses: {{sample.output_json}}

Score from 0 to 1 based on:
- 1.0: The reference disease appears in the top 3 diagnoses (exact match or very close synonym)
- 0.7: The reference disease appears in positions 4-10
- 0.3: A related/similar disease appears but not the exact match
- 0.0: The reference disease doesn't appear at all

Consider medical synonyms and alternative names when matching."""
                    }
                ],
                "range": [0, 1],
                "pass_threshold": 0.5
            },
            "valid_format": {
                "name": "Valid Format",
                "type": "python",
                "source": """
def grade(sample, item):
    try:
        diagnoses = sample.get('output_json', {}).get('diagnoses', [])
        if not isinstance(diagnoses, list) or len(diagnoses) == 0:
            return 0.0
        # Check if all diagnoses have required fields
        for d in diagnoses:
            if not isinstance(d, dict) or 'disease_name' not in d or 'rank' not in d:
                return 0.0
        return 1.0
    except:
        return 0.0
"""
            }
        },
        "calculate_output": "0.9 * disease_match + 0.1 * valid_format"
    }
    
    return grader_config


def validate_grader(grader: Dict, api_key: Optional[str] = None) -> bool:
    """Validate the grader configuration using OpenAI's validation endpoint.
    
    Args:
        grader: The grader configuration to validate
        api_key: Optional API key (if not set in environment)
    
    Returns:
        bool: True if validation successful, False otherwise
    """
    # Get API key
    if api_key:
        openai_api_key = api_key
    else:
        openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY not found")
    
    # Prepare headers
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }
    
    # Prepare payload
    payload = {"grader": grader}
    
    print("\nValidating grader configuration...")
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/fine_tuning/alpha/graders/validate",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            print("✓ Grader validation successful!")
            return True
        else:
            print(f"✗ Grader validation failed!")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error validating grader: {e}")
        return False


def upload_file(client: OpenAI, file_path: str) -> str:
    """Upload a file for fine-tuning and return the file ID."""
    print(f"Uploading file: {file_path}")
    
    with open(file_path, "rb") as f:
        response = client.files.create(
            file=f,
            purpose="fine-tune"
        )
    
    file_id = response.id
    print(f"File uploaded successfully. File ID: {file_id}")
    
    # Wait a moment for file processing
    time.sleep(2)
    
    return file_id


def create_json_schema() -> Dict:
    """Create the JSON schema for structured outputs."""
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "medical_diagnosis",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "diagnoses": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "rank": {
                                    "type": "integer",
                                    "description": "Rank of the diagnosis (1 = most likely)"
                                },
                                "disease_name": {
                                    "type": "string",
                                    "description": "Name of the disease"
                                }
                            },
                            "required": ["rank", "disease_name"],
                            "additionalProperties": False
                        },
                        "minItems": 1,
                        "description": "List of candidate diagnoses ranked by probability"
                    }
                },
                "required": ["diagnoses"],
                "additionalProperties": False
            }
        }
    }


def create_rft_job(
    client: OpenAI,
    training_file_id: str,
    validation_file_id: str,
    model: str = "o4-mini-2025-04-16",
    suffix: Optional[str] = None,
    use_structured_output: bool = True,
    reasoning_effort: str = "medium"
) -> str:
    """Create the reinforcement fine-tuning job."""
    
    print(f"\nCreating RFT job with:")
    print(f"  Model: {model}")
    print(f"  Training file: {training_file_id}")
    print(f"  Validation file: {validation_file_id}")
    print(f"  Structured output: {use_structured_output}")
    print(f"  Reasoning effort: {reasoning_effort}")
    
    # Prepare the job configuration
    job_config = {
        "training_file": training_file_id,
        "validation_file": validation_file_id,
        "model": model,
        "method": {
            "type": "reinforcement",
            "reinforcement": {
                "grader": create_structured_output_grader() if use_structured_output else create_fuzzy_match_grader(),
                "hyperparameters": {
                    "reasoning_effort": reasoning_effort
                }
            }
        }
    }
    
    # Add structured output configuration if enabled
    if use_structured_output:
        job_config["method"]["reinforcement"]["response_format"] = create_json_schema()
    
    # Add suffix if provided
    if suffix:
        job_config["suffix"] = suffix
    
    # Create the fine-tuning job
    try:
        response = client.fine_tuning.jobs.create(**job_config)
        job_id = response.id
        print(f"\nFine-tuning job created successfully!")
        print(f"Job ID: {job_id}")
        print(f"Status: {response.status}")
        
        return job_id
        
    except Exception as e:
        print(f"Error creating fine-tuning job: {e}")
        raise


def monitor_job(client: OpenAI, job_id: str, check_interval: int = 60):
    """Monitor the fine-tuning job until completion."""
    print(f"\nMonitoring job {job_id}...")
    print("Press Ctrl+C to stop monitoring (job will continue running)")
    
    try:
        while True:
            job = client.fine_tuning.jobs.retrieve(job_id)
            status = job.status
            
            print(f"\nStatus: {status}")
            
            if status in ["succeeded", "failed", "cancelled"]:
                print(f"\nJob completed with status: {status}")
                
                if status == "succeeded":
                    print(f"Fine-tuned model: {job.fine_tuned_model}")
                elif status == "failed":
                    print(f"Error: {job.error}")
                
                break
            
            # Get recent events
            events = client.fine_tuning.jobs.list_events(
                fine_tuning_job_id=job_id,
                limit=5
            )
            
            if events.data:
                print("\nRecent events:")
                for event in reversed(events.data):
                    print(f"  {event.created_at}: {event.message}")
            
            print(f"\nChecking again in {check_interval} seconds...")
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print("\nStopped monitoring. Job will continue running in the background.")
        print(f"Check status at: https://platform.openai.com/finetune/{job_id}")


def main():
    parser = argparse.ArgumentParser(
        description="Create a reinforcement fine-tuning job for o4-mini"
    )
    parser.add_argument(
        "--train-file",
        type=str,
        default="data/rft/rft_train.jsonl",
        help="Path to training JSONL file"
    )
    parser.add_argument(
        "--valid-file",
        type=str,
        default="data/rft/rft_valid.jsonl",
        help="Path to validation JSONL file"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="o4-mini-2025-04-16",
        help="Base model to fine-tune"
    )
    parser.add_argument(
        "--suffix",
        type=str,
        help="Optional suffix for the fine-tuned model name"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenAI API key (or set OPENAI_API_KEY env var)"
    )
    parser.add_argument(
        "--no-structured-output",
        action="store_true",
        help="Disable structured output (use plain text matching)"
    )
    parser.add_argument(
        "--reasoning-effort",
        type=str,
        default="high",
        choices=["low", "medium", "high"],
        help="Reasoning effort level for o4 models"
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Monitor the job after creation"
    )
    parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="Skip file upload (provide file IDs instead)"
    )
    parser.add_argument(
        "--train-file-id",
        type=str,
        default="file-1vCuVJY1FkQeGWeDPtVHni",
        help="Training file ID (if --skip-upload). Default: file-1vCuVJY1FkQeGWeDPtVHni"
    )
    parser.add_argument(
        "--valid-file-id",
        type=str,
        default="file-DsX2HU3bh782RxPx1wPnFm",
        help="Validation file ID (if --skip-upload). Default: file-DsX2HU3bh782RxPx1wPnFm"
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip grader validation (not recommended)"
    )
    
    args = parser.parse_args()
    
    # Set up API key
    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key
    elif not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY not found. Set it via --api-key or environment variable.")
    
    # Initialize client
    client = OpenAI()
    
    # Create and validate grader before uploading files
    if not args.skip_validation:
        grader = create_structured_output_grader() if not args.no_structured_output else create_fuzzy_match_grader()
        if not validate_grader(grader, args.api_key):
            print("\nGrader validation failed. Please fix the grader configuration and try again.")
            print("You can skip validation with --skip-validation, but this is not recommended.")
            return
    
    # Get file IDs
    if args.skip_upload:
        train_file_id = args.train_file_id
        valid_file_id = args.valid_file_id
        print(f"Using existing files:")
        print(f"  Training file ID: {train_file_id}")
        print(f"  Validation file ID: {valid_file_id}")
    else:
        # Check if files exist
        if not Path(args.train_file).exists():
            raise FileNotFoundError(f"Training file not found: {args.train_file}")
        if not Path(args.valid_file).exists():
            raise FileNotFoundError(f"Validation file not found: {args.valid_file}")
        
        # Upload files
        train_file_id = upload_file(client, args.train_file)
        valid_file_id = upload_file(client, args.valid_file)
    
    # Create the RFT job
    job_id = create_rft_job(
        client,
        train_file_id,
        valid_file_id,
        model=args.model,
        suffix=args.suffix,
        use_structured_output=not args.no_structured_output,
        reasoning_effort=args.reasoning_effort
    )
    
    # Monitor if requested
    if args.monitor:
        monitor_job(client, job_id)
    else:
        print(f"\nJob created! Monitor at: https://platform.openai.com/finetune/{job_id}")
        print(f"Or run: python {__file__} --monitor --job-id {job_id}")


if __name__ == "__main__":
    main()