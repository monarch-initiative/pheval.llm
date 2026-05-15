from __future__ import annotations
from datetime import datetime, date
import re
from pathlib import Path
import json


class CURIE:
    PATTERNS = {
        "HP": r"^HP:\d{7}$",
        "OMIM": r"^OMIM:\d{6}$",
        "HGNC": r"^HGNC:\d+$",
    }

    def __new__(cls, value: str):
        prefix = value.split(":")[0]
        pattern = cls.PATTERNS.get(prefix, r"^[A-Z]+:\S+$")
        if not re.match(pattern, value):
            raise ValueError(f"Invalid {prefix}: {value}")
        return str(value)


class Phenopacket:
    def __init__(self, data: dict, filepath: Path | None = None):
        self.data = data
        self.filepath = filepath
        self._cached_pmid_date = None

    @property
    def id(self) -> str:
        return self.data.get("id")

    @property
    def disease_ids(self) -> list[CURIE | None]:
        diseases = self.data.get("diseases", [])
        return [
            CURIE(d.get("term", {}).get("id")) if d.get("term", {}).get("id") else None
            for d in diseases
        ]

    @property
    def gene_ids(self) -> list[str | None]:
        interpretations = self.data.get("interpretations", [])
        genomic_interpretations = [
            i.get("diagnosis", {}).get("genomicInterpretations", []) for i in interpretations
        ]
        return [
            g.get("variantInterpretation", {})
            .get("variationDescriptor", {})
            .get("geneContext", {})
            .get("valueId", {})
            for g in genomic_interpretations
        ]

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
