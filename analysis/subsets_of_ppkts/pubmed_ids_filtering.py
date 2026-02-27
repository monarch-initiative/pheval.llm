from pathlib import Path
import pandas as pd
import os
import json

hpoa_path = Path(
    "/Users/leonardo/git/BOQA/data/human-phenotype-ontology/latest_20260211/phenotype.hpoa"
)
store_path = Path("/Users/leonardo/git/BOQA/data/phenopacket-store/latest_20260211/0.1.26")

hpoa_df = pd.read_csv(hpoa_path, header=4, sep="\t", usecols=["reference"])
hpoa_set = set(hpoa_df["reference"])


# Extract PMIDs from externalReferences
def get_ref_ids_from_phenopacket(pkt_data):
    """Extract all ref IDs from externalReferences"""
    ref_ids = []
    external_refs = pkt_data.get("metaData", {}).get("externalReferences", [])
    for ref in external_refs:
        ref_id = ref.get("id", "")
        ref_ids.append(ref_id)
    return ref_ids


phenopackets = []
for root, dirs, files in os.walk(store_path):
    for filename in files:
        if filename.endswith(".json"):
            file_path = os.path.join(root, filename)
            with open(file_path, "r") as f:
                pkt_data = json.load(f)
                pkt_data["_filename"] = filename  # Store the original filename
                pkt_data["_absolute_path"] = os.path.abspath(file_path)  # Store absolute path
                # Only append phenopackets that have a pubmedid not in the hpoa_set
                ref_ids = get_ref_ids_from_phenopacket(pkt_data)
                # print(f"Sample ref_ids: {ref_ids[:3]}")
                # print(f"Sample hpoa_set entries: {list(hpoa_set)[:3]}")
                # breakpoint()
                if any(refid not in hpoa_set for refid in ref_ids):
                    phenopackets.append(pkt_data)

print(len(phenopackets))
