import time
from typing import List, Tuple

from curategpt.store import get_store
from oaklib.interfaces.text_annotator_interface import (
    TextAnnotationConfiguration,
    TextAnnotatorInterface,
)

from malco.process.cleaning import clean_diagnosis_line


def perform_curategpt_grounding(
    diagnosis: str,
    path: str,
    collection: str,
    database_type: str = "chromadb",
    limit: int = 1,
    relevance_factor: float = 0.23,
    verbose: bool = False,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    timeout: float = 10.0,
) -> List[Tuple[str, str]]:
    """
    Use curategpt to perform grounding for a given diagnosis when initial attempts fail.

    Parameters:
    - diagnosis: The diagnosis text to ground.
    - path: The path to the database. You'll need to create an index of Mondo using curategpt in this db
    - collection: The collection to search within curategpt. Name of mondo collection in the db
    NB: You can make this collection by running curategpt thusly:
    `curategpt ontology index --index-fields label,definition,relationships -p stagedb -c ont_mondo -m openai: sqlite:obo:mondo`
    - database_type: The type of database used for grounding (e.g., chromadb, duckdb).
    - limit: The number of search results to return.
    - relevance_factor: The distance threshold for relevance filtering.
    - verbose: Whether to print verbose output for debugging.
    - max_retries: Maximum number of retry attempts.
    - retry_delay: Delay between retries in seconds.
    - timeout: Timeout for each attempt in seconds.

    Returns:
    - List of tuples: [(Mondo ID, Label), ...]
    """

    for attempt in range(max_retries + 1):
        try:
            if verbose and attempt > 0:
                print(
                    f"CurateGPT grounding attempt {attempt + 1}/{max_retries + 1} for: {diagnosis}"
                )

            # Initialize the database store
            db = get_store(database_type, path)

            # Perform the search using the provided diagnosis
            # Note: We don't have direct timeout control over the search call,
            # but we can catch common timeout and connection errors
            results = db.search(diagnosis, collection=collection)

            # Filter results based on relevance factor (distance)
            if relevance_factor is not None:
                results = [
                    (obj, distance, _meta)
                    for obj, distance, _meta in results
                    if distance <= relevance_factor
                ]

            # Limit the results to the specified number (limit)
            limited_results = results[:limit]

            # Extract Mondo IDs and labels
            pred_ids = []
            pred_labels = []

            for obj, _distance, _meta in limited_results:
                disease_mondo_id = obj.get(
                    "original_id"
                )  # Use the 'original_id' field for Mondo ID
                disease_label = obj.get("label")

                if disease_mondo_id and disease_label:
                    pred_ids.append(disease_mondo_id)
                    pred_labels.append(disease_label)

            # Return as a list of tuples (Mondo ID, Label)
            if len(pred_ids) == 0:
                if verbose:
                    print(f"No grounded IDs found for {diagnosis}")
                return [("N/A", "No grounding found")]

            return list(zip(pred_ids, pred_labels))

        except Exception as e:
            error_message = str(e).lower()

            # Check if this is a retryable error
            is_retryable = any(
                keyword in error_message
                for keyword in [
                    "timeout",
                    "connection",
                    "network",
                    "api",
                    "rate limit",
                    "temporary",
                    "unavailable",
                    "overloaded",
                    "busy",
                ]
            )

            if attempt < max_retries and is_retryable:
                if verbose:
                    print(f"Retryable error on attempt {attempt + 1} for '{diagnosis}': {str(e)}")
                    print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                # Exponential backoff: double the delay for the next retry
                retry_delay *= 2
                continue
            else:
                # Either max retries reached or non-retryable error
                if verbose:
                    print(
                        f"CurateGPT grounding failed for '{diagnosis}' after {attempt + 1} attempts: {str(e)}"
                    )
                return [("N/A", "CurateGPT grounding failed")]

    # This should not be reached, but just in case
    return [("N/A", "CurateGPT grounding failed")]


# Perform grounding on the text to MONDO ontology and return the result
def perform_oak_grounding(
    annotator: TextAnnotatorInterface,
    diagnosis: str,
    exact_match: bool,
    verbose: bool,
    include_list: List[str],
) -> List[Tuple[str, str]]:
    """
    Perform grounding for a diagnosis. The 'exact_match' flag controls whether exact or inexact
    (partial) matching is used. Filter results to include only CURIEs that match the 'include_list',
    and exclude results that match the 'exclude_list'.
    Remove redundant groundings from the result.
    """
    config = TextAnnotationConfiguration(matches_whole_text=exact_match)
    annotations = list(annotator.annotate_text(diagnosis, configuration=config))

    # Filter and remove duplicates, while excluding unwanted general terms
    filtered_annotations = list(
        {
            (ann.object_id, ann.object_label)
            for ann in annotations
            if any(ann.object_id.startswith(prefix) for prefix in include_list)
        }
    )

    if filtered_annotations:
        return filtered_annotations
    else:
        match_type = "exact" if exact_match else "inexact"
        if verbose:
            print(f"No {match_type} grounded IDs found for: {diagnosis}")
            pass
        return [("N/A", "No grounding found")]


# Now, integrate curategpt into your ground_diagnosis_text_to_mondo function
def ground_diagnosis_text_to_mondo(
    annotator: TextAnnotatorInterface,
    differential_diagnosis: str,
    verbose: bool,
    include_list: List[
        str
    ] = None,  # B006 Do not use mutable data structures for argument defaults.
    use_ontogpt_grounding: bool = True,
    curategpt_path: str = "stagedb/",
    curategpt_collection: str = "ont_mondo",
    curategpt_database_type: str = "chromadb",
) -> List[Tuple[str, List[Tuple[str, str]]]]:

    # See https://docs.python.org/3/tutorial/controlflow.html#default-argument-values
    if include_list is None:
        include_list = ["MONDO:"]

    results = []

    headers_to_avoid = [
        "differential diagnosis",
        "here is the list",
        "here is a list",
        "here are the" "based on the clinical features",
        "based on the symptoms",
        "based on the given case",
        "based on the limited information",
        "based on the clinical presentation",
        "based on the case",
        # "based on the provided case study",
        "based on the provided",
        "here are the candidate diagnoses",
        "listed by probability",
        "candidate diagnoses",
        "potential diagnoses",
        "ranked by likelihood",
        "these conditions are",
        "note: ",
        "i'm sorry",
        # "please note",
        "please",
        "given the complexity",
        "these diseases are",
        "if you have",
        "if further details",
        "the list above",
        "these disorders are",
    ]
    # Split the input into lines and process each one
    # TODO: Track line number of diagnoses in case
    for line in differential_diagnosis.splitlines():
        clean_line = clean_diagnosis_line(line)

        # Skip header lines like "**Differential diagnosis:**"
        if not clean_line or any(x in clean_line.lower() for x in headers_to_avoid):
            continue

        # Try grounding the full line first (exact match)
        grounded = perform_oak_grounding(
            annotator, clean_line, exact_match=True, verbose=verbose, include_list=include_list
        )

        # Try grounding with curategpt if no grounding is found
        if use_ontogpt_grounding and grounded == [("N/A", "No grounding found")]:
            grounded = perform_curategpt_grounding(
                diagnosis=clean_line,
                path=curategpt_path,
                collection=curategpt_collection,
                database_type=curategpt_database_type,
                verbose=verbose,
            )

        # If still no grounding is found, log the final failure
        if grounded == [("N/A", "No grounding found")]:
            if verbose:
                print(f"Final grounding failed for: {clean_line}")

        # Append the grounded results (even if no grounding was found)
        results.append((clean_line, grounded))

    return results
