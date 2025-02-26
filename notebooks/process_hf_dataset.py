from datasets import Dataset, DatasetDict
import os



folder_path = "../prompts/"
prompts = []

for filename in os.listdir(folder_path):
    if filename.endswith(".txt"):
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "r") as file:
            content = file.read()
            prompts.append(content)

data = {
    "text": prompts,
}
dataset = Dataset.from_dict(data)
dataset_dict = DatasetDict({
    "validation": dataset
})    
#dataset.save_to_disk("dataset/")
dataset_dict.push_to_hub("apizza/exomiser-benchmark")