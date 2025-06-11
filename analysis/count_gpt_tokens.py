import tiktoken
import os

# Choose the encoding for your model (e.g., gpt-3.5-turbo, gpt-4, etc.)
encoding = tiktoken.encoding_for_model("gpt-4o")

langs = ["en", "cs", "de", "es", "fr", "it", "ja", "tr", "zh", "nl"]

# For each language count and save the tokens in all files in the directory
directory = "in_multlingual_nov24/prompts/"

count_dict_input = {}
count_dict_output = {}

for lang in langs:
    # INPUT COST
    total_tokens = 0
    langpath = os.path.join(directory, lang)
    for filename in os.listdir(langpath): # For all files
        if filename.endswith(f"_{lang}-prompt.txt"):
            with open(os.path.join(langpath, filename), 'r', encoding='utf-8') as file:
                text = file.read()
                num_tokens = len(encoding.encode(text))
                total_tokens += num_tokens
    count_dict_input[lang] = total_tokens
    print(f"Total input tokens for {lang}: {total_tokens}")

    # OUTPUT COST
    total_tokens = 0
    outpath = f"out_multlingual_nov24/raw_results/multilingual/{lang}/differentials_by_file/"
    for filename in os.listdir(outpath): 
        if filename.endswith(f"_{lang}-prompt.txt.result"):
            with open(os.path.join(outpath, filename), 'r', encoding='utf-8') as file:
                text = file.read()
                num_tokens = len(encoding.encode(text, allowed_special={'<|endoftext|>'}))
                total_tokens += num_tokens
    count_dict_output[lang] = total_tokens
    print(f"Total output tokens for {lang}: {total_tokens}")


count_dict_input['total'] = sum(count_dict_input.values())
count_dict_output['total'] = sum(count_dict_output.values())

print(f"Full input token count: {count_dict_input['total']}") 
print(f"Full output token count: {count_dict_output['total']}") 

# Save the dictionaries to files
input_file = "analysis_out/token_counts/input_token_counts.txt"
output_file = "analysis_out/token_counts/output_token_counts.txt"
os.makedirs(os.path.dirname(input_file), exist_ok=True)
os.makedirs(os.path.dirname(output_file), exist_ok=True)
with open(input_file, 'w') as f:
    f.write("Input cost for GPT-4o $5.00 / 1M input tokens\n")
    for lang, count in count_dict_input.items():
        f.write(f"{lang}: {count}\n")
print(f"Input token counts saved to {input_file}")
with open(output_file, 'w') as f:
    f.write("Output cost for GPT-4o $20.00 / 1M output tokens\n")
    for lang, count in count_dict_output.items():
        f.write(f"{lang}: {count}\n")
print(f"Output token counts saved to {output_file}")