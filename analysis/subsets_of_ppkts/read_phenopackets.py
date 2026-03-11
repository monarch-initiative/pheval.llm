from pathlib import Path
import json
import os


def read_phenopackets(input_path: Path) -> list:
    phenopackets = []
    for root, dirs, files in os.walk(input_path):
        for filename in files:
            if filename.endswith(".json"):
                file_path = os.path.join(root, filename)
                with open(file_path, "r") as f:
                    pkt_data = json.load(f)
                    pkt_data["_filename"] = filename  # Store the original filename
                    pkt_data["_absolute_path"] = os.path.abspath(file_path)  # Store absolute path
                    phenopackets.append(pkt_data)
    return phenopackets
