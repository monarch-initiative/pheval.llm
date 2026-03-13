# Summary stats of a set of phenopackets defined via absolute paths in a txt file
from __future__ import annotations
from pathlib import Path
import json
from datetime import datetime, date
import matplotlib.pyplot as plt
import argparse
from collections import Counter
from collections import defaultdict
import numpy as np

pmid_date_file = Path(__file__).parent / "pmid2date_dict.json"

"""TODO ppkts per disease, 
number of diseases, 
disease category as in hpo descendant of different categories in children of phenotypic abnormality
number of hpos in hpoa count distribution for all diseases present in cohort"""


class Phenopacket:
    def __init__(self, data: dict, filepath: Path | None = None):
        self.data = data
        self.filepath = filepath
        self._cached_pmid_date = None

    @property
    def id(self) -> str:
        return self.data.get("id")

    @property
    def disease_ids(self) -> list[str | None]:
        diseases = self.data.get("diseases", [])
        return [d.get("term", {}).get("id") for d in diseases]

    @property
    def curation_date(self) -> date:
        metadata = self.data.get("metaData", {})
        date_str = metadata.get("created")
        return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()

    @property  # no state change, no arguemts
    def number_observed_hpos(self) -> int:
        return sum(
            1 for i in self.data.get("phenotypicFeatures", []) if not i.get("excluded", False)
        )

    def publication_date(self, pmid2date: dict) -> date | None:
        """Get publication date from external reference PMID."""
        metadata = self.data.get("metaData", {})
        ext_refs = metadata.get("externalReferences", [])
        for ref in ext_refs:
            pmid = ref.get("id", "")
            if pmid.startswith("PMID:") and pmid in pmid2date:
                date_str = pmid2date[pmid]["date"]
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").date()
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
        ppkt._cached_pmid_date = ppkt.publication_date(pmid2date)

    return phenopacket_list


def phenopackets_per_disease(ppkts: list[Phenopacket], max_bin: int = 10) -> list[int]:
    """
    Returns histogram counts where:
    index 0 -> diseases with 1 phenopacket
    index 1 -> diseases with 2 phenopackets
    ...
    index max_bin-2 -> diseases with max_bin-1 phenopackets
    index max_bin-1 -> diseases with >= max_bin phenopackets
    """
    disease_counter = Counter()

    for p in ppkts:
        for d in p.disease_ids:
            if d:
                disease_counter[d] += 1

    hist = [0] * max_bin

    for count in disease_counter.values():
        if count >= max_bin:
            hist[max_bin - 1] += 1
        else:
            hist[count - 1] += 1

    return hist


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate comparison statistics for two phenopacket cohorts"
    )
    parser.add_argument(
        "--txt_file1",
        type=Path,
        help="Path to first txt file with phenopacket paths",
        default="/Users/leonardo/data/subsets_of_ppkts_0.1.26/disjunctive_union_v2/phenopackets_hpoa.txt",
    )
    parser.add_argument(
        "--txt_file2",
        type=Path,
        help="Path to second txt file with phenopacket paths",
        default="/Users/leonardo/git/BOQA/ppkts0_1_26ppkts.txt",
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

    all_hpo_counts = []
    all_pmid_dates = []
    all_curation_dates = []

    for ppkts, _ in datasets:
        all_hpo_counts.extend([p.number_observed_hpos for p in ppkts])
        all_pmid_dates.extend([p._cached_pmid_date for p in ppkts if p._cached_pmid_date])
        all_curation_dates.extend([p.curation_date for p in ppkts])

    # PLOTTING
    fig1, axes1 = plt.subplots(2, 2, figsize=(14, 8))  # 2 rows, 2 columns

    for idx, (ppkts, name) in enumerate(datasets):
        # pick the left-most axes in the row
        ax_row = axes1[idx, 0]  # left column of the row
        ax_row.text(
            -0.12,  # x offset in axes coords (negative to go left)
            0.5,  # y center of the axes
            name,
            va="center",
            ha="center",
            rotation="vertical",
            fontsize=12,
            fontweight="bold",
            transform=ax_row.transAxes,  # important! use axes coordinates
        )

        # 1st column: HPO term counts
        hpo_counts = [p.number_observed_hpos for p in ppkts]
        axes1[idx, 0].hist(hpo_counts, bins=20, range=(min(all_hpo_counts), max(all_hpo_counts)))
        axes1[idx, 0].set_title(f"Term number distribution (n={len(ppkts)})")
        axes1[idx, 0].set_xlabel("Number of HPO terms")
        axes1[idx, 0].set_ylabel("Number of cases")

        # 2nd column: phenopackets per disease
        max_bin = 30
        hist = phenopackets_per_disease(ppkts, max_bin=max_bin)
        x_labels = [str(i) for i in range(1, max_bin)] + [f">={str(max_bin)}"]
        x_positions = list(range(max_bin))  # 0..max_bin-1

        axes1[idx, 1].bar(x_positions, hist)
        axes1[idx, 1].set_xticks(x_positions)
        axes1[idx, 1].set_xticklabels(x_labels)
        axes1[idx, 1].set_title("Phenopackets per disease")
        axes1[idx, 1].set_xlabel("Phenopackets per disease")
        axes1[idx, 1].set_yscale("log")
        axes1[idx, 1].set_ylabel("Number of diseases (log scale)")
        # axes1[idx, 1].set_ylabel("Number of diseases")

    plt.tight_layout()
    plt.show()

    fig2, axes2 = plt.subplots(2, 2, figsize=(14, 8))  # 2 rows, 2 columns

    for idx, (ppkts, name) in enumerate(datasets):
        # pick the left-most axes in the row
        ax_row = axes2[idx, 0]  # left column of the row
        ax_row.text(
            -0.12,  # x offset in axes coords (negative to go left)
            0.5,  # y center of the axes
            name,
            va="center",
            ha="center",
            rotation="vertical",
            fontsize=12,
            fontweight="bold",
            transform=ax_row.transAxes,  # important! use axes coordinates
        )
        # left column: PMID dates
        pmid_dates = [p._cached_pmid_date for p in ppkts if p._cached_pmid_date]
        axes2[idx, 0].hist(pmid_dates, bins=50, range=(min(all_pmid_dates), max(all_pmid_dates)))
        axes2[idx, 0].set_title(f"PMID publication date (n={len(pmid_dates)})")
        axes2[idx, 0].set_xlabel("Date")
        axes2[idx, 0].set_ylabel("Number of cases")

        # --- compute PMIDs per year and average HPOs for THIS dataset ---
        year_to_hpo_counts = defaultdict(list)
        for p in ppkts:
            pub_date = p._cached_pmid_date
            if pub_date:
                year_to_hpo_counts[pub_date.year].append(p.number_observed_hpos)

        # Ensure consecutive years (even if no PMIDs that year)
        min_year = min(year_to_hpo_counts.keys())
        max_year = max(year_to_hpo_counts.keys())
        all_years = list(range(min_year, max_year + 1))
        x_pos = np.arange(len(all_years))

        num_pmids_per_year = [
            len(year_to_hpo_counts[y]) if y in year_to_hpo_counts else 0 for y in all_years
        ]
        avg_hpos_per_year = [
            np.mean(year_to_hpo_counts[y]) if y in year_to_hpo_counts else np.nan for y in all_years
        ]

        # left axis: bars
        ax1 = ax_row
        bar_width = 0.6
        ax1.bar(x_pos, num_pmids_per_year, color="#4da6ff", alpha=0.8, width=bar_width)
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(all_years, rotation=45)
        ax1.set_xlabel("Publication year")
        ax1.set_ylabel("Number of PMIDs", color="blue")
        ax1.tick_params(axis="y", labelcolor="blue")

        # right axis: line
        ax2 = ax1.twinx()
        ax2.plot(
            x_pos,
            avg_hpos_per_year,
            color="orange",
            marker="o",
            label="Avg HPOs",
            linewidth=2,
            linestyle="None",
        )
        ax2.set_ylabel("Average number of HPOs", color="orange")
        ax2.tick_params(axis="y", labelcolor="orange")

        # force x-limits identical for both axes
        ax1.set_xlim(-0.5, len(all_years) - 0.5)

        ax1.grid(axis="y", linestyle="--", alpha=0.5)
        ax1.set_title(f"Publication year vs PMIDs & Avg HPOs (n={len(ppkts)})")

        # right column: curation dates
        curation_dates = [p.curation_date for p in ppkts]
        axes2[idx, 1].hist(
            curation_dates, bins=50, range=(min(all_curation_dates), max(all_curation_dates))
        )
        axes2[idx, 1].set_title(f"Curation date distribution (n={len(curation_dates)})")
        axes2[idx, 1].set_xlabel("Date")
        axes2[idx, 1].set_yscale("log")
        axes2[idx, 1].set_ylabel("Number of cases (log)")

    plt.tight_layout()
    plt.show()

    # fig, axes = plt.subplots(2, 4, figsize=(18, 10))
    # for idx, (ppkts, name) in enumerate(datasets):
    #     # Place the text to the left of the row (figure coordinates)
    #     fig.text(
    #         0.01,  # x-position: just left of the subplots
    #         0.75 - idx * 0.5,  # y-position: roughly center of row
    #         name,  # label
    #         va="center",
    #         ha="left",  # vertical + horizontal alignment
    #         rotation="vertical",  # rotate for side label
    #         fontsize=12,
    #         fontweight="bold",
    #     )
    #     plt.subplots_adjust(left=0.12, right=0.95, hspace=0.3, wspace=0.35)

    #     hpo_counts = [p.number_observed_hpos for p in ppkts]
    #     pmid_dates = [p._cached_pmid_date for p in ppkts if p._cached_pmid_date]
    #     curation_dates = [p.curation_date for p in ppkts]

    #     axes[idx, 0].hist(hpo_counts, bins=20, range=(min(all_hpo_counts), max(all_hpo_counts)))
    #     axes[idx, 0].set_title(f"Term number distribution (n={len(ppkts)})")
    #     axes[idx, 0].set_xlabel("Number of HPO Terms")
    #     axes[idx, 0].set_ylabel("Number of cases")

    #     axes[idx, 1].hist(pmid_dates, bins=50, range=(min(all_pmid_dates), max(all_pmid_dates)))
    #     axes[idx, 1].set_title(f"PMID date distribution (n={len(pmid_dates)})")
    #     axes[idx, 1].set_xlabel("Date")
    #     axes[idx, 1].set_ylabel("Number of cases")

    #     axes[idx, 2].hist(
    #         curation_dates, bins=50, range=(min(all_curation_dates), max(all_curation_dates))
    #     )
    #     axes[idx, 2].set_title(f"Curation date distribution (n={len(curation_dates)})")
    #     axes[idx, 2].set_xlabel("Date")
    #     axes[idx, 2].set_ylabel("Number of cases")

    #     # ppkts per disease
    #     max_bin = 25
    #     hist = phenopackets_per_disease(ppkts, max_bin)

    #     x_labels = [str(i) for i in range(1, max_bin)] + [f">={max_bin}"]
    #     axes[idx, 3].bar(range(max_bin), hist)
    #     axes[idx, 3].set_xticks(range(max_bin))
    #     axes[idx, 3].set_xticklabels(x_labels)

    #     axes[idx, 3].set_title(f"Phenopackets per disease")
    #     axes[idx, 3].set_xlabel("Number of phenopackets")
    #     axes[idx, 3].set_yscale("log")
    #     axes[idx, 3].set_ylabel("Number of diseases (log scale)")
    #     # axes[idx, 3].set_ylabel("Number of diseases")

    # plt.tight_layout()
    # plt.show()
