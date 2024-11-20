from oaklib.datamodels.vocabulary import IS_A
from oaklib.interfaces import MappingProviderInterface
from pathlib import Path

from typing import List
from cachetools.keys import hashkey


FULL_SCORE = 1.0
PARTIAL_SCORE = 0.5


def omim_mappings(term: str, adapter) -> List[str]:
    """
    Get the OMIM mappings for a term.

    Example:

    >>> from oaklib import get_adapter
    >>> omim_mappings("MONDO:0007566", get_adapter("sqlite:obo:mondo"))
    ['OMIM:132800']

    Args:
        term (str): The term.
        adapter: The mondo adapter.

    Returns:
        str: The OMIM mappings.
    """
    omims = []
    for m in adapter.sssom_mappings([term], source="OMIM"):
        if m.predicate_id == "skos:exactMatch":
            omims.append(m.object_id)
    return omims


def score_grounded_result(prediction: str, ground_truth: str, mondo, cache=None) -> float:
    """
    Score the grounded result.

    Exact match:
    >>> from oaklib import get_adapter
    >>> score_grounded_result("OMIM:132800", "OMIM:132800", get_adapter("sqlite:obo:mondo"))
    1.0

    The predicted Mondo is equivalent to the ground truth OMIM
    (via skos:exactMatches in Mondo):

    >>> score_grounded_result("MONDO:0007566", "OMIM:132800", get_adapter("sqlite:obo:mondo"))
    1.0

    The predicted Mondo is a disease entity that groups multiple
    OMIMs, one of which is the ground truth:

    >>> score_grounded_result("MONDO:0008029", "OMIM:158810", get_adapter("sqlite:obo:mondo"))
    0.5

    Args:
        prediction (str): The prediction.
        ground_truth (str): The ground truth.
        mondo: The mondo adapter.

    Returns:
        float: The score.
    """
    if not isinstance(mondo, MappingProviderInterface):
        raise ValueError("Adapter is not an MappingProviderInterface")

    if prediction == ground_truth:
        # predication is the correct OMIM
        return FULL_SCORE

    ground_truths = get_ground_truth_from_cache_or_compute(prediction, mondo, cache)
    if ground_truth in ground_truths:
        # prediction is a MONDO that directly maps to a correct OMIM
        return FULL_SCORE

    descendants_list = mondo.descendants([prediction], predicates=[IS_A], reflexive=True)
    for mondo_descendant in descendants_list:
        ground_truths = get_ground_truth_from_cache_or_compute(mondo_descendant, mondo, cache)
        if ground_truth in ground_truths:
            # prediction is a MONDO that maps to a correct OMIM via a descendant
            return PARTIAL_SCORE
    return 0.0


def get_ground_truth_from_cache_or_compute(
    term,
    adapter,
    cache,
):
    if cache is None:
        return omim_mappings(term, adapter)

    k = hashkey(term)
    try:
        ground_truths = cache[k]
        cache.hits += 1
    except KeyError:
        # cache miss
        ground_truths = omim_mappings(term, adapter)
        cache[k] = ground_truths
        cache.misses += 1
    return ground_truths
