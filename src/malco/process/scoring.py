import logging
from pathlib import Path
import pandas as pd
from cachetools import LRUCache
from cachetools.keys import hashkey
from oaklib import get_adapter
from oaklib.interfaces import OboGraphInterface
from shelved_cache import PersistentCache
from malco.process.mondo_score_utils import score_grounded_result
from tqdm import tqdm

FULL_SCORE = 1.0
PARTIAL_SCORE = 0.5


def cache_info(self):
    return f"CacheInfo: hits={self.hits}, misses={self.misses}, maxsize={self.wrapped.maxsize}, currsize={self.wrapped.currsize}"


def mondo_adapter() -> OboGraphInterface:
    """
    Get the adapter for the MONDO ontology.

    Returns:
        Adapter: The adapter.
    """
    return get_adapter("sqlite:obo:mondo")

def score(df) -> pd.DataFrame:
    """
    Score the results of the grounding.
    """
    out_caches = Path("caches")
    out_caches.mkdir(exist_ok=True)
    pc2_cache_file = str(out_caches / "score_grounded_result_cache")
    pc2 = PersistentCache(LRUCache, pc2_cache_file, maxsize=524288)
    pc1_cache_file = str(out_caches / "omim_mappings_cache")
    pc1 = PersistentCache(LRUCache, pc1_cache_file, maxsize=524288)
    pc1.hits = pc1.misses = 0
    pc2.hits = pc2.misses = 0
    PersistentCache.cache_info = cache_info
    pc1.initialize_if_not_initialized()
    pc2.initialize_if_not_initialized()
    print(pc1.cache_info())
    print(pc2.cache_info())
    df['scored'] = None
    mondo = mondo_adapter()
    for index, row in tqdm(df.iterrows(), total=df.shape[0], desc=f"Scoring Grounded Results"):
        grounded_diagnoses = row['grounding']

        if not row["gold"]:
            logging.warning(f"No correct ID found for metadata: {row['id']}")
            continue  # Skip rows with no correct ID

        results = []
        # Loop through each grounded diagnosis and score them
        for rank, (disease_name, grounded_list) in enumerate(grounded_diagnoses, start=1):
            for grounded_id, _ in grounded_list:
                k = hashkey(grounded_id, row["gold"]["disease_id"])
                try:
                    grounded_score = pc2[k]
                    pc2.hits += 1
                except KeyError:
                    grounded_score = score_grounded_result(grounded_id, row["gold"]["disease_id"], mondo, pc1)
                    pc2[k] = grounded_score
                    pc2.misses += 1

                is_correct = grounded_score > 0  # Score > 0 means either exact or subclass match
                result_row = {"rank": rank, "grounded_id": grounded_id, "grounded_score": grounded_score, "is_correct": is_correct}
                results.append(result_row)
        df.at[index, "scored"] = results
    pc1.close()
    pc2.close()
    return df
