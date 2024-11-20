import zipfile
import os
import requests

phenopacket_zip_url = "https://github.com/monarch-initiative/phenopacket-store/releases/download/0.1.11/all_phenopackets.zip"
# TODO just point to a folder w/ ppkts
phenopacket_dir = "phenopacket-store"


def setup_phenopackets(self) -> str:
    phenopacket_store_path = os.path.join(self.input_dir, phenopacket_dir)
    if os.path.exists(phenopacket_store_path):
        print(f"{phenopacket_store_path} exists, skipping download.")
    else:
        print(f"{phenopacket_store_path} doesn't exist, downloading phenopackets...")
        download_phenopackets(self, phenopacket_zip_url, phenopacket_dir)
    return phenopacket_store_path


def download_phenopackets(self, phenopacket_zip_url, phenopacket_dir):
    # Ensure the directory for storing the phenopackets exists
    phenopacket_store_path = os.path.join(self.input_dir, phenopacket_dir)
    os.makedirs(phenopacket_store_path, exist_ok=True)

    # Download the phenopacket release zip file
    response = requests.get(phenopacket_zip_url)
    zip_path = os.path.join(self.input_dir, "all_phenopackets.zip")
    with open(zip_path, "wb") as f:
        f.write(response.content)
    print("Download completed.")

    # Unzip the phenopacket release zip file
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(phenopacket_store_path)
    print("Unzip completed.")
