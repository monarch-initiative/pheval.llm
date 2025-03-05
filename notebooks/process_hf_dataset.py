from datasets import Dataset, DatasetDict


hub_location = "apizza/exomiser-benchmark"
dataset = Dataset.from_json("data/exomiser-gold.jsonl")

dataset_dict = DatasetDict({
    "validation": dataset
})

#dataset.save_to_disk("dataset/")
dataset_dict.push_to_hub(hub_location)