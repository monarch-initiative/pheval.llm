# Summary stats of a set of phenopackets defined via absolute paths in a txt file
from __future__ import annotations
from pathlib import Path
import json
import datetime
import matplotlib.pyplot as plt
import argparse

pmid_date_file = Path("/Users/leonardo/git/malco/leakage_experiment/pmid2date_dict.json")


class Phenopacket:
    def __init__(self, data: dict, filepath: Path | None = None):
        self.data = data
        self.filepath = filepath
        self._cached_date = None

    @property
    def id(self) -> str:
        return self.data.get("id")

    @property  # no state change, no arguemts
    def number_observed_hpos(self) -> int:
        return sum(
            1 for i in self.data.get("phenotypicFeatures", []) if not i.get("excluded", False)
        )

    def publication_date(self, pmid2date: dict) -> datetime.date | None:
        """Get publication date from external reference PMID."""
        metadata = self.data.get("metaData", {})
        ext_refs = metadata.get("externalReferences", [])
        for ref in ext_refs:
            pmid = ref.get("id", "")
            if pmid.startswith("PMID:") and pmid in pmid2date:
                date_str = pmid2date[pmid]["date"]
                return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").date()
        return None

    @classmethod
    def from_file(cls, filepath: Path) -> Phenopacket:
        with open(filepath, "r") as f:
            ppkt_data = json.load(f)
        return cls(ppkt_data, filepath)


def load_phenopackets(txt_file: Path, pmid2date: dict) -> list[Phenopacket]:
    with open(txt_file, "r") as ppkt_file:
        phenopacket_list = [Phenopacket.from_file(Path(line.strip())) for line in ppkt_file]

    for ppkt in phenopacket_list:
        ppkt._cached_date = ppkt.publication_date(pmid2date)

    return phenopacket_list


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate comparison statistics for two phenopacket cohorts"
    )
    parser.add_argument(
        "--txt_file1", type=Path, help="Path to first txt file with phenopacket paths",
        default="/Users/leonardo/data/subsets_of_ppkts_0.1.26/disjunctive_union_v2/phenopackets_hpoa.txt"
    )
    parser.add_argument(
        "--txt_file2", type=Path, help="Path to second txt file with phenopacket paths",
        default="/Users/leonardo/git/BOQA/ppkts0_1_26ppkts.txt"
    )
    parser.add_argument(
        "--pmid-dates",
        type=Path,
        default=pmid_date_file,
        help="Path to PMID to date mapping JSON file",
    )

    args = parser.parse_args()

    with open(args.pmid_dates, "r") as f:
        pmid2date = json.load(f)

    ppkts1 = load_phenopackets(args.txt_file1, pmid2date)
    ppkts2 = load_phenopackets(args.txt_file2, pmid2date)

    datasets = [
        (ppkts1, args.txt_file1.stem),
        (ppkts2, args.txt_file2.stem),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    for idx, (ppkts, name) in enumerate(datasets):
        hpo_counts = [p.number_observed_hpos for p in ppkts]
        dates = [p._cached_date for p in ppkts if p._cached_date]

        axes[idx, 0].hist(hpo_counts, bins=20)
        axes[idx, 0].set_title(f"{name}\nHPO Terms (n={len(ppkts)})")
        axes[idx, 0].set_xlabel("Number of HPO Terms")
        axes[idx, 0].set_ylabel("Count")

        axes[idx, 1].hist(dates, bins=50)
        axes[idx, 1].set_title(f"{name}\nPublication Dates (n={len(dates)})")
        axes[idx, 1].set_xlabel("Date")
        axes[idx, 1].set_ylabel("Count")

    plt.tight_layout()
    plt.show()
