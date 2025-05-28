"""Split a JSONL file into multiple files based on language tags in the 'id' field.
This script reads a JSONL file, extracts lines that contain specific language tags in the 'id' field, and writes them to separate files for each language.
The script takes three command-line arguments:
1. The directory containing the input JSONL file.
2. The name of the input JSONL file.
3. A comma-separated list of languages to filter by.

Example usage:
python split_jsonl_multilingual.py /path/to/data/ input_file.jsonl "en,es,fr"
"""

from pathlib import Path
import json
import sys


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Parse input:
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
default_languages = ['en', 'cs', 'es', 'de', 'it', 'ja', 'nl', 'tr', 'zh', 'fr'] 
try:
    data_dir = str(sys.argv[1])
except IndexError:
    data_dir = "/Users/leonardo/data/meditron/multilingual/"
    print('\nYou can pass the data directory as a first CLI argument!\n')
try:
    file_name = str(sys.argv[2])
except IndexError:
    file_name = "multilingual-exomiser-meditron-70b.jsonl"
    print('\nYou can pass the file name as a second CLI argument!\n')
try:
    languages_str = sys.argv[3]
    # Split the string into a list
    languages = languages_str.split(',')
except IndexError:
    # If no argument is provided, use the default languages
    languages = default_languages
    print('\nYou can pass a comma-separated list of languages as a second CLI argument!\n')

print(f"Using languages: {languages}")
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
breakpoint()
with open(data_dir + file_name, 'r') as f:
    # Create a dictionary to hold file handles for each language
    file_handles = {lang: open(data_dir + lang + "-meditron-70b.jsonl", 'w') for lang in languages}

    try:
        for line in f:
            data = json.loads(line)
            for lang in languages:
                if lang  + "-prompt.txt" in data['id']:
                    file_handles[lang].write(line)
                    break
    finally:
        # Close all file handles
        for handle in file_handles.values():
            handle.close()
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



    