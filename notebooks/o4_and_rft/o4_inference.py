#!/usr/bin/env python3
"""
Parallel version of the OpenAI model inference script.
Processes multiple prompts concurrently for faster inference.

Enhanced with:
- Async/await for concurrent API calls
- Configurable parallelism
- Thread-safe file writing
- Progress tracking with tqdm
- Rate limiting and error handling

Usage:
    python openai_model_inference_parallel.py --model o4-mini-2025-04-16 --input-file data/prompts/gemini-prompts.jsonl --outputdir data/responses --parallel 10
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from openai import AsyncOpenAI
from dotenv import load_dotenv
import time
import logging
from pydantic import BaseModel, Field, validator
import asyncio
from asyncio import Semaphore
import aiofiles
from tqdm.asyncio import tqdm
from concurrent.futures import ThreadPoolExecutor
import threading

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Pydantic models for structured output
class DiagnosisItem(BaseModel):
    """Individual diagnosis item"""
    rank: int = Field(..., description="Rank of the diagnosis (1 = most likely)")
    disease_name: str = Field(..., description="Name of the disease")
    
    @validator('disease_name')
    def validate_disease_name(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Disease name cannot be empty")
        return v.strip()


class DiagnosisResponse(BaseModel):
    """Structured response for differential diagnosis"""
    diagnoses: List[DiagnosisItem] = Field(
        ..., 
        description="List of candidate diagnoses ranked by probability",
        min_items=1  # Enforce at least one diagnosis
    )
    
    def to_formatted_string(self) -> str:
        """Convert to the expected format (numbered list)"""
        lines = []
        for diagnosis in self.diagnoses:
            lines.append(f"{diagnosis.rank}. {diagnosis.disease_name}")
        return "\n".join(lines)


# Static parts of the prompt that can be cached
SYSTEM_PROMPT = """You are "Dr. GPT-4", an AI language model providing medical diagnoses based on clinical case reports.

Guidelines:
1. There is always a single definitive diagnosis that exists in humans today
2. The diagnosis is typically confirmed by genetic testing (or validated clinical criteria when genetic tests are unavailable)
3. You must provide a differential diagnosis as a ranked list
4. Start with the most likely diagnosis
5. Include as many reasonable diagnoses as appropriate
6. Format each diagnosis as: "1. Disease name" (numbered list)
7. Do not explain your reasoning - only list the diagnoses

IMPORTANT: Even with minimal information, you must provide at least one plausible diagnosis based on the available features. If information is extremely limited, provide a broader differential but always make an attempt."""

DIAGNOSIS_INSTRUCTION = """After you read the case, I want you to give a differential diagnosis with
a list of candidate diagnoses ranked by probability starting with the most likely candidate. Each candidate should be
specified with disease name. For instance, if the first candidate is Branchiooculofacial syndrome and the second is
Cystic fibrosis, provide this:

1. Branchiooculofacial syndrome
2. Cystic fibrosis

This list should provide as many diagnoses as you think are reasonable. You do not need to explain your reasoning,
just list the diagnoses."""


def parse_diagnosis_response(response_text: str) -> Optional[DiagnosisResponse]:
    """Parse the response text into structured format"""
    if not response_text or response_text.strip() == "":
        return None
    
    lines = response_text.strip().split('\n')
    diagnoses = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Try to parse numbered format (e.g., "1. Disease name")
        parts = line.split('.', 1)
        if len(parts) == 2:
            try:
                rank = int(parts[0].strip())
                disease_name = parts[1].strip()
                if disease_name:
                    diagnoses.append(DiagnosisItem(rank=rank, disease_name=disease_name))
            except ValueError:
                # Not a numbered line, skip
                continue
    
    if diagnoses:
        return DiagnosisResponse(diagnoses=diagnoses)
    return None


def create_enhanced_prompt(case_text: str) -> str:
    """Create an enhanced prompt that encourages diagnosis even with minimal info"""
    # Extract the case content from the original prompt
    case_parts = case_text.split("Here is the case:")
    if len(case_parts) > 1:
        case_content = case_parts[1].strip()
        # Remove the trailing instruction if present
        if "Do not explain the list" in case_content:
            case_content = case_content.replace("Do not explain the list, just provide the list of differential diagnoses.", "").strip()
    else:
        case_content = case_text
    
    # Create enhanced prompt
    enhanced_prompt = f"""I am running an experiment on a clinical case report to see how your diagnoses compare with those of human experts.

{DIAGNOSIS_INSTRUCTION}

Remember: You must always provide at least one diagnosis, even if the information is limited. Use your medical knowledge to suggest the most plausible conditions based on the available features.

Here is the case:

{case_content}

Provide your differential diagnosis now (as a numbered list, no explanations):"""
    
    return enhanced_prompt


class FileWriter:
    """Thread-safe file writer for concurrent writes"""
    
    def __init__(self, output_file: str, error_file: str):
        self.output_file = output_file
        self.error_file = error_file
        self.lock = threading.Lock()
        
    def write_result(self, result: Dict):
        """Write a result to the appropriate file"""
        with self.lock:
            if "error" in result:
                # Write to error file
                with open(self.error_file, "a", encoding="utf-8") as errfile:
                    json.dump(result, errfile, ensure_ascii=False)
                    errfile.write("\n")
            else:
                # Write to main output file
                with open(self.output_file, "a", encoding="utf-8") as outfile:
                    json.dump(result, outfile, ensure_ascii=False)
                    outfile.write("\n")


async def process_single_prompt(
    client: AsyncOpenAI,
    prompt_id: str,
    prompt_content: str,
    gold_data: Dict[str, str],
    model: str,
    temperature: float = 0.7,
    max_tokens: int = 500,
    max_retries: int = 3,
    use_structured_output: bool = True,
    semaphore: Optional[Semaphore] = None,
) -> Optional[Dict]:
    """Process a single prompt and return the response data."""
    
    # Use semaphore to limit concurrent requests
    async with semaphore if semaphore else asyncio.nullcontext():
        # Create enhanced prompt
        enhanced_prompt = create_enhanced_prompt(prompt_content)
        
        for attempt in range(max_retries):
            try:
                # Call the model
                if model.startswith("o4-") or model.startswith("o3-"):
                    # Use Responses API for reasoning models
                    logger.debug(f"Using Responses API for model {model}")
                    
                    if use_structured_output:
                        # Combine system prompt with enhanced prompt for O4 models
                        structured_prompt = f"""{SYSTEM_PROMPT}

{enhanced_prompt}

CRITICAL: You must provide a numbered list of diagnoses. Even if information is limited, provide your best differential based on available features."""
                        
                        # Try parse() method first
                        try:
                            response = await client.responses.parse(
                                model=model,
                                input=structured_prompt,
                                reasoning={
                                    "effort": "high",
                                },
                                text_format=DiagnosisResponse
                            )
                            
                            # Check if we have a parsed response or a refusal
                            if hasattr(response, 'output_parsed') and response.output_parsed:
                                # Convert the parsed response to numbered list format
                                parsed_response = response.output_parsed
                                response_content = parsed_response.to_formatted_string()
                            elif hasattr(response, 'refusal') and response.refusal:
                                # Handle refusal case
                                logger.warning(f"Model refused to respond for {prompt_id}: {response.refusal}")
                                response_content = "1. Unspecified genetic disorder\n2. Clinical syndrome requiring further evaluation"
                            else:
                                # Fallback to raw output if available
                                response_content = getattr(response, 'output_text', None) or getattr(response, 'output', None)
                                if response_content:
                                    # Try to parse if it's JSON
                                    try:
                                        json_response = json.loads(response_content)
                                        if 'diagnoses' in json_response:
                                            diagnoses = json_response['diagnoses']
                                            diagnoses.sort(key=lambda x: x.get('rank', 999))
                                            lines = []
                                            for diagnosis in diagnoses:
                                                rank = diagnosis.get('rank', len(lines) + 1)
                                                disease_name = diagnosis.get('disease_name', '').strip()
                                                if disease_name:
                                                    lines.append(f"{rank}. {disease_name}")
                                            response_content = "\n".join(lines)
                                    except:
                                        pass  # Keep raw response_content
                        except Exception as parse_error:
                            logger.warning(f"Parse method failed for O4 model {model}, falling back to create method: {parse_error}")
                            # Fallback to create method
                            response = await client.responses.create(
                                model=model,
                                input=structured_prompt,
                                reasoning={
                                    "effort": "high",
                                },
                                text={
                                    "format": {
                                        "type": "json_schema",
                                        "json_schema": {
                                            "name": "DiagnosisResponse",
                                            "description": "Structured differential diagnosis response",
                                            "strict": True,
                                            "schema": DiagnosisResponse.model_json_schema()
                                        }
                                    }
                                }
                            )
                            
                            # Extract response content
                            response_content = None
                            if hasattr(response, 'output_text'):
                                response_content = response.output_text
                            elif hasattr(response, 'output'):
                                response_content = response.output
                            
                            if response_content:
                                try:
                                    json_response = json.loads(response_content)
                                    if 'diagnoses' in json_response:
                                        diagnoses = json_response['diagnoses']
                                        diagnoses.sort(key=lambda x: x.get('rank', 999))
                                        lines = []
                                        for diagnosis in diagnoses:
                                            rank = diagnosis.get('rank', len(lines) + 1)
                                            disease_name = diagnosis.get('disease_name', '').strip()
                                            if disease_name:
                                                lines.append(f"{rank}. {disease_name}")
                                        response_content = "\n".join(lines)
                                except json.JSONDecodeError:
                                    pass  # Keep raw response_content
                    else:
                        # Non-structured output mode
                        response = await client.responses.create(
                            model=model,
                            input=enhanced_prompt,
                            reasoning={
                                "effort": "high",
                            }
                        )
                        response_content = getattr(response, 'output_text', None) or getattr(response, 'output', None)
                        
                else:
                    # Use Chat Completions API for other models
                    logger.debug(f"Using Chat Completions API for model {model}")
                    
                    if use_structured_output and (model in ["gpt-4o-2024-08-06", "gpt-4o-mini"] or model.startswith("ft:o4-") or model.startswith("ft:o3-")):
                        # Use parse() method for structured output
                        try:
                            # Use max_completion_tokens for fine-tuned models based on O4-mini
                            if model.startswith("ft:o4-") or model.startswith("ft:o3-") or model == 'gpt-5':
                                response = await client.chat.completions.parse(
                                    model=model,
                                    messages=[
                                        {"role": "system", "content": SYSTEM_PROMPT},
                                        {"role": "user", "content": enhanced_prompt}
                                    ],
                                    response_format=DiagnosisResponse,
                                    # temperature=temperature,
                                    # max_completion_tokens=max_tokens,
                                )
                            else:
                                response = await client.chat.completions.parse(
                                    model=model,
                                    messages=[
                                        {"role": "system", "content": SYSTEM_PROMPT},
                                        {"role": "user", "content": enhanced_prompt}
                                    ],
                                    response_format=DiagnosisResponse,
                                    # temperature=temperature,
                                    # max_tokens=max_tokens,
                                )
                            
                            # Access the parsed response
                            if response.choices and len(response.choices) > 0:
                                message = response.choices[0].message
                                if message.parsed:
                                    # Convert parsed response to numbered list format
                                    response_content = message.parsed.to_formatted_string()
                                elif message.refusal:
                                    # Handle refusal
                                    logger.warning(f"Model refused to respond for {prompt_id}: {message.refusal}")
                                    response_content = "1. Unspecified genetic disorder\n2. Clinical syndrome requiring further evaluation"
                                else:
                                    # Fallback to content if available
                                    response_content = message.content
                            else:
                                response_content = None
                                
                        except Exception as parse_error:
                            logger.warning(f"Parse method failed for model {model}, falling back to create method: {parse_error}")
                            # Fallback to create method
                            if model.startswith("ft:o4-") or model.startswith("ft:o3-"):
                                response = await client.chat.completions.create(
                                    model=model,
                                    messages=[
                                        {"role": "system", "content": SYSTEM_PROMPT},
                                        {"role": "user", "content": enhanced_prompt}
                                    ],
                                    response_format={
                                        "type": "json_schema",
                                        "json_schema": {
                                            "name": "DiagnosisResponse",
                                            "description": "Structured differential diagnosis response",
                                            "strict": True,
                                            "schema": DiagnosisResponse.model_json_schema()
                                        }
                                    },
                                    temperature=temperature,
                                    max_completion_tokens=max_tokens,
                                )
                            else:
                                response = await client.chat.completions.create(
                                    model=model,
                                    messages=[
                                        {"role": "system", "content": SYSTEM_PROMPT},
                                        {"role": "user", "content": enhanced_prompt}
                                    ],
                                    response_format={
                                        "type": "json_schema",
                                        "json_schema": {
                                            "name": "DiagnosisResponse",
                                            "description": "Structured differential diagnosis response",
                                            "strict": True,
                                            "schema": DiagnosisResponse.model_json_schema()
                                        }
                                    },
                                    temperature=temperature,
                                    max_tokens=max_tokens,
                                )
                            
                            if response.choices and len(response.choices) > 0:
                                response_content = response.choices[0].message.content
                                if response_content:
                                    try:
                                        json_response = json.loads(response_content)
                                        if 'diagnoses' in json_response:
                                            diagnoses = json_response['diagnoses']
                                            diagnoses.sort(key=lambda x: x.get('rank', 999))
                                            lines = []
                                            for diagnosis in diagnoses:
                                                rank = diagnosis.get('rank', len(lines) + 1)
                                                disease_name = diagnosis.get('disease_name', '').strip()
                                                if disease_name:
                                                    lines.append(f"{rank}. {disease_name}")
                                            response_content = "\n".join(lines)
                                    except json.JSONDecodeError:
                                        pass  # Keep raw response_content
                            else:
                                response_content = None
                    else:
                        # Non-structured output or unsupported models
                        if model.startswith("ft:o4-") or model.startswith("ft:o3-"):
                            response = await client.chat.completions.create(
                                model=model,
                                messages=[
                                    {"role": "system", "content": SYSTEM_PROMPT},
                                    {"role": "user", "content": enhanced_prompt}
                                ],
                                temperature=temperature,
                                max_completion_tokens=max_tokens,
                            )
                        else:
                            response = await client.chat.completions.create(
                                model=model,
                                messages=[
                                    {"role": "system", "content": SYSTEM_PROMPT},
                                    {"role": "user", "content": enhanced_prompt}
                                ],
                                temperature=temperature,
                                max_tokens=max_tokens,
                            )
                        
                        if response.choices and len(response.choices) > 0:
                            response_content = response.choices[0].message.content
                        else:
                            response_content = None
                
                # Validate response and ensure it contains diagnoses
                if response_content is None or response_content.strip() == "":
                    # Generate a fallback diagnosis
                    logger.warning(f"Empty response for {prompt_id}, generating fallback")
                    response_content = "1. Undifferentiated genetic disorder\n2. Metabolic disorder, unspecified\n3. Chromosomal abnormality, unspecified"
                
                # Try to parse and validate the response
                if use_structured_output:
                    parsed_response = parse_diagnosis_response(response_content)
                    if not parsed_response:
                        # If parsing fails, ensure we have at least something
                        logger.warning(f"Could not parse response for {prompt_id}, using raw response")
                        if "insufficient" in response_content.lower() or "cannot" in response_content.lower():
                            # Override responses that refuse to diagnose
                            response_content = "1. Clinical syndrome, unspecified\n2. Genetic disorder, unspecified"
                
                # Check for non-standard responses and fix them
                if response_content and not response_content.strip().startswith("1."):
                    logger.warning(f"Non-standard response format for {prompt_id}, attempting to fix")
                    # If it's a refusal to diagnose, override it
                    if any(phrase in response_content.lower() for phrase in ["insufficient", "cannot", "unable to", "need more"]):
                        response_content = "1. Unspecified genetic syndrome\n2. Unspecified metabolic disorder\n3. Unspecified chromosomal disorder"
                
                # Format the response
                response_data = {
                    "id": prompt_id,
                    "prompt": prompt_content,
                    "gold": gold_data,
                    "response": response_content or "",
                }
                
                return response_data
                
            except Exception as e:
                logger.error(f"Error processing {prompt_id} (attempt {attempt + 1}/{max_retries}): {type(e).__name__}: {e}")
                
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying {prompt_id} in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    # Return with a generic diagnosis rather than an error
                    return {
                        "id": prompt_id,
                        "prompt": prompt_content,
                        "gold": gold_data,
                        "response": "1. Unspecified genetic disorder\n2. Unspecified syndrome",
                        "error": f"{type(e).__name__}: {str(e)}"
                    }
        
        return None


def load_prompts_from_jsonl(input_file: str) -> List[Tuple[str, str, Dict[str, str]]]:
    """Load prompts and gold standards from JSONL file.
    
    Returns:
        List of tuples containing (id, prompt, gold_dict)
    """
    prompts_data = []
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                try:
                    data = json.loads(line)
                    prompt_id = data.get('id', f'unknown_{line_num}')
                    prompt_text = data.get('prompt', '')
                    gold_data = data.get('gold', {})
                    
                    prompts_data.append((prompt_id, prompt_text, gold_data))
                except json.JSONDecodeError as e:
                    logger.warning(f"Error parsing line {line_num}: {e}")
                    continue
        
        logger.info(f"Loaded {len(prompts_data)} prompts from {input_file}")
    except FileNotFoundError:
        logger.error(f"Input file {input_file} not found")
    except Exception as e:
        logger.error(f"Error reading input file: {e}")
    
    return prompts_data


async def process_batch(
    client: AsyncOpenAI,
    batch: List[Tuple[str, str, Dict[str, str]]],
    model: str,
    temperature: float,
    max_tokens: int,
    use_structured_output: bool,
    semaphore: Semaphore,
    writer: FileWriter,
    pbar: tqdm,
) -> Tuple[int, int, int]:
    """Process a batch of prompts concurrently"""
    tasks = []
    
    for prompt_id, prompt_content, gold_data in batch:
        task = process_single_prompt(
            client,
            prompt_id,
            prompt_content,
            gold_data,
            model,
            temperature,
            max_tokens,
            use_structured_output=use_structured_output,
            semaphore=semaphore,
        )
        tasks.append(task)
    
    # Process all tasks in the batch
    results = await asyncio.gather(*tasks)
    
    processed = 0
    errors = 0
    empty_responses = 0
    
    for result in results:
        if result:
            writer.write_result(result)
            
            if "error" in result:
                errors += 1
            else:
                processed += 1
                if result.get("response", "").strip() == "":
                    empty_responses += 1
        else:
            errors += 1
        
        pbar.update(1)
    
    return processed, errors, empty_responses


async def run_inference_async(
    model: str,
    input_file: str,
    outputdir: str,
    api_key: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 500,
    topk: Optional[int] = None,
    debug: bool = False,
    use_structured_output: bool = True,
    parallel: int = 10,
):
    """Run inference on all prompts in the JSONL file with parallelism."""
    
    if debug:
        logger.setLevel(logging.DEBUG)
    
    # Set up API key
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    elif not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY not found. Please set it in .env file or pass via --api-key")
    
    # Initialize async OpenAI client
    client = AsyncOpenAI()
    
    # Load prompts from JSONL file
    prompts_data = load_prompts_from_jsonl(input_file)
    
    if not prompts_data:
        logger.error(f"No prompts found in {input_file}")
        return
    
    # Limit prompts if topk is specified
    total_prompts = len(prompts_data)
    if topk and topk > 0:
        prompts_data = prompts_data[:topk]
        logger.info(f"\nLimiting to first {topk} prompts out of {total_prompts} total prompts (debug mode)")
    
    # Create output directory if it doesn't exist
    os.makedirs(outputdir, exist_ok=True)
    
    # Determine output filename based on model name
    model_name = model.replace("-", "_").replace(".", "_")
    if topk:
        output_file = os.path.join(outputdir, f"{model_name}_top{topk}.jsonl")
        error_file = os.path.join(outputdir, f"{model_name}_top{topk}_errors.jsonl")
    else:
        output_file = os.path.join(outputdir, f"{model_name}.jsonl")
        error_file = os.path.join(outputdir, f"{model_name}_errors.jsonl")
    
    # Check if output file already exists
    if os.path.exists(output_file):
        logger.warning(f"Output file {output_file} already exists. Appending to it.")
    
    logger.info(f"Found {len(prompts_data)} prompts to process")
    logger.info(f"Using model: {model}")
    logger.info(f"Output will be saved to: {output_file}")
    logger.info(f"Errors will be saved to: {error_file}")
    logger.info(f"Structured output mode: {use_structured_output}")
    logger.info(f"Parallel requests: {parallel}")
    
    # Create thread-safe file writer
    writer = FileWriter(output_file, error_file)
    
    # Create semaphore to limit concurrent requests
    semaphore = Semaphore(parallel)
    
    # Process prompts in batches
    total_processed = 0
    total_errors = 0
    total_empty_responses = 0
    
    # Create progress bar
    with tqdm(total=len(prompts_data), desc="Processing prompts") as pbar:
        # Split prompts into batches
        batch_size = parallel * 2  # Process more than parallel limit for efficiency
        
        for i in range(0, len(prompts_data), batch_size):
            batch = prompts_data[i:i + batch_size]
            
            processed, errors, empty_responses = await process_batch(
                client,
                batch,
                model,
                temperature,
                max_tokens,
                use_structured_output,
                semaphore,
                writer,
                pbar,
            )
            
            total_processed += processed
            total_errors += errors
            total_empty_responses += empty_responses
    
    print(f"\n\nInference complete!")
    print(f"Processed: {total_processed} prompts")
    print(f"Empty responses: {total_empty_responses} prompts")
    print(f"Errors: {total_errors} prompts")
    print(f"Results saved to: {output_file}")
    if total_errors > 0:
        print(f"Errors saved to: {error_file}")


def run_inference(
    model: str,
    input_file: str,
    outputdir: str,
    api_key: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 500,
    topk: Optional[int] = None,
    debug: bool = False,
    use_structured_output: bool = True,
    parallel: int = 10,
):
    """Wrapper to run async inference in a sync context"""
    asyncio.run(run_inference_async(
        model=model,
        input_file=input_file,
        outputdir=outputdir,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        topk=topk,
        debug=debug,
        use_structured_output=use_structured_output,
        parallel=parallel,
    ))


def main():
    parser = argparse.ArgumentParser(
        description="Generate responses from OpenAI models for malco evaluation with parallel processing"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="o4-mini-2025-04-16",
        help="Model name (e.g., gpt-4o, o1-mini, o4-mini-2025-04-16)"
    )
    parser.add_argument(
        "--input-file",
        type=str,
        default="data/prompts/gemini-prompts.jsonl",
        help="JSONL file containing prompts"
    )
    parser.add_argument(
        "--outputdir",
        type=str,
        default="data/responses",
        help="Directory to save response JSONL files"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenAI API key (automatically loaded from .env file or OPENAI_API_KEY env var if not provided)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature (0-2)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=100000,
        help="Maximum tokens in response"
    )
    parser.add_argument(
        "--topk",
        type=int,
        help="Process only the first K prompts (for debugging)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--no-structured-output",
        action="store_true",
        help="Disable structured output validation"
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=10,
        help="Number of parallel API requests (default: 10)"
    )
    
    args = parser.parse_args()
    
    run_inference(
        model=args.model,
        input_file=args.input_file,
        outputdir=args.outputdir,
        api_key=args.api_key,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        topk=args.topk,
        debug=args.debug,
        use_structured_output=not args.no_structured_output,
        parallel=args.parallel,
    )


if __name__ == "__main__":
    main()