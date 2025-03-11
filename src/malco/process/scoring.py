import logging
from pathlib import Path
import pandas as pd
from cachetools import LRUCache
from cachetools.keys import hashkey
from oaklib import get_adapter
from oaklib.interfaces import OboGraphInterface
from shelved_cache import PersistentCache
from malco.process.mondo_score_utils import score_grounded_result
from malco.config.malco_config import MalcoConfig
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

# def compute_mrr_and_ranks(
#     df: pd.DataFrame,
#     comparing: str,
#     run_config: MalcoConfig,
# ) -> Tuple[Path, Path, dict, Path]:
#     """
#     Go from the slightly preprocessed data to a dataframe with ranks, correct results, and most importantly, score the results.
#
#     The scoring happens in score_grounded_result().
#     """
#     out_caches = Path("caches")
#     out_caches.mkdir(exist_ok=True)
#     output_dir = run_config.output_dir
#     results_data = []
#     results_files = []
#     num_ppkt = {}
#     pc2_cache_file = str(out_caches / "score_grounded_result_cache")
#     pc2 = PersistentCache(LRUCache, pc2_cache_file, maxsize=524288)
#     pc1_cache_file = str(out_caches / "omim_mappings_cache")
#     pc1 = PersistentCache(LRUCache, pc1_cache_file, maxsize=524288)
#     pc1.hits = pc1.misses = 0
#     pc2.hits = pc2.misses = 0
#     PersistentCache.cache_info = cache_info
#     # Calculate the Mean Reciprocal Rank (MRR) for each file
#     mrr_scores = []
#     header = [
#         comparing,
#         "n1",
#         "n2",
#         "n3",
#         "n4",
#         "n5",
#         "n6",
#         "n7",
#         "n8",
#         "n9",
#         "n10",
#         "n10p",
#         "nf",
#         "num_cases",
#         "grounding_failed"
#     ]
#     rank_df = pd.DataFrame(0, index=arange(len(results_files)), columns=header)
#
#     cache_file = out_caches / "cache_log.txt"
#
#     with cache_file.open("a", newline="") as cf:
#         now_is = datetime.now().strftime("%Y%m%d-%H%M%S")
#         cf.write("Timestamp: " + now_is + "\n\n")
#         mondo = mondo_adapter()
#         i = 0
#         # Each df is a model or a language
#         # TODO: Iterate on the row of the dataframe which is one model and a line is one response
#         for df in results_data:
#             # TODO: Get the grounding result
#             # For each label in the results file, find if the correct term is ranked
#             df["rank"] = df.groupby("label")["score"].rank(ascending=False, method="first")
#             #
#             label_4_non_eng = df["label"].str.replace(
#                 "_[a-z][a-z]-prompt", "_en-prompt", regex=True
#             )
#
#             # df['correct_term'] is an OMIM
#             # df['term'] is Mondo or OMIM ID, or even disease label
#             df["correct_term"] = label_4_non_eng.map(label_to_correct_term, na_action="ignore")
#
#             # Make sure caching is used in the following by unwrapping explicitly
#             results = []
#             # TODO this will be our tuples
#             for _idx, row in df.iterrows():
#                 # call OAK and get OMIM IDs for df['term'] and see if df['correct_term'] is one of them
#                 # in the case of phenotypic series, if Mondo corresponds to grouping term, accept it
#                 k = hashkey(row["term"], row["correct_term"])
#                 try:
#                     val = pc2[k]
#                     pc2.hits += 1
#                 except KeyError:
#                     # cache miss
#                     val = score_grounded_result(row["term"], row["correct_term"], mondo, pc1)
#                     pc2[k] = val
#                     pc2.misses += 1
#                 is_correct = val > 0
#                 results.append(is_correct)
#
#             df["is_correct"] = results
#             df["reciprocal_rank"] = df.apply(
#                 lambda row: 1 / row["rank"] if row["is_correct"] else 0, axis=1
#             )
#
#             # This should not be necessary any more (this gets rid of cases where there is a bug in the phenopacket).
#             # Necessary for data of previous runs, before the aforementioned bugs were removed.
#             df.dropna(subset=["correct_term"])  # this should not be necessary
#
#             # Save full data frame
#             full_df_path = output_dir / results_files[i].split("/")[0]
#             full_df_filename = "full_df_results.tsv"
#             safe_save_tsv(full_df_path, full_df_filename, df)
#
#             # Calculate MRR for this file
#             mrr = df.groupby("label")["reciprocal_rank"].max().mean()
#             mrr_scores.append(mrr)
#
#             # Calculate top<n> of each rank
#             rank_df.loc[i, comparing] = results_files[i].split("/")[0]
#
#             ppkts = df.groupby("label")[["term", "rank", "is_correct"]]
#
#             # for each group
#             for ppkt in ppkts:
#                 # is there a true? ppkt is tuple ("filename", dataframe) --> ppkt[1] is a dataframe
#                 if not any(ppkt[1]["is_correct"]):
#                     if all(ppkt[1]["term"].str.startswith("MONDO")):
#                         # no  --> increase nf = "not found"
#                         rank_df.loc[i, "nf"] += 1
#                     else:
#                         rank_df.loc[i, "grounding_failed"] += 1
#                 else:
#                     # yes --> what's it rank? It's <j>
#                     jind = ppkt[1].index[ppkt[1]["is_correct"]]
#                     j = int(ppkt[1]["rank"].loc[jind].values[0])
#                     if j < 11:
#                         # increase n<j>
#                         rank_df.loc[i, "n" + str(j)] += 1
#                     else:
#                         # increase n10p
#                         rank_df.loc[i, "n10p"] += 1
#
#             # Write cache charatcteristics to file
#             cf.write(results_files[i])
#             cf.write("\nscore_grounded_result cache info:\n")
#             cf.write(str(pc2.cache_info()))
#             cf.write("\nomim_mappings cache info:\n")
#             cf.write(str(pc1.cache_info()))
#             cf.write("\n\n")
#             i = i + 1
#
#     pc1.close()
#     pc2.close()
#
#     for modelname in num_ppkt.keys():
#         rank_df.loc[rank_df[comparing] == modelname, "num_cases"] = num_ppkt[modelname]
#     data_dir = output_dir / "rank_data"
#     data_dir.mkdir(exist_ok=True)
#     topn_file_name = "topn_result.tsv"
#     topn_file = data_dir / topn_file_name
#     safe_save_tsv(data_dir, topn_file_name, rank_df)
#
#     print("MRR scores are:\n")
#     print(mrr_scores)
#     mrr_file = data_dir / "mrr_result.tsv"
#
#     # write out results for plotting
#     with mrr_file.open("w", newline="") as dat:
#         writer = csv.writer(dat, quoting=csv.QUOTE_NONNUMERIC, delimiter="\t", lineterminator="\n")
#         writer.writerow(results_files)
#         writer.writerow(mrr_scores)
#
#     df = pd.read_csv(topn_file, delimiter="\t")
#     #valid_cases = df["num_cases"] - df["grounding_failed"]
#     valid_cases = df["num_cases"]
#     df["top1"] = (df["n1"]) / valid_cases
#     df["top3"] = (df["n1"] + df["n2"] + df["n3"]) / valid_cases
#     df["top5"] = (df["n1"] + df["n2"] + df["n3"] + df["n4"] + df["n5"]) / valid_cases
#     df["top10"] = (
#         df["n1"]
#         + df["n2"]
#         + df["n3"]
#         + df["n4"]
#         + df["n5"]
#         + df["n6"]
#         + df["n7"]
#         + df["n8"]
#         + df["n9"]
#         + df["n10"]
#     ) / valid_cases
#     df["not_found"] = (df["nf"]+df['grounding_failed']) / valid_cases
#
#     df_aggr = pd.DataFrame()
#     df_aggr = pd.melt(
#         df,
#         id_vars=comparing,
#         value_vars=["top1", "top3", "top5", "top10", "not_found"],
#         var_name="Rank_in",
#         value_name="percentage",
#     )
#
#     # If "topn_aggr.tsv" already exists, prepend "old_"
#     # It's the user's responsibility to know only up to 2 versions can exist, then data is lost
#     topn_aggr_file_name = "topn_aggr.tsv"
#     topn_aggr_file = data_dir / topn_aggr_file_name
#     safe_save_tsv(data_dir, topn_aggr_file_name, df_aggr)
#
#     return mrr_file, data_dir, num_ppkt, topn_aggr_file
