import re
from typing import Tuple

# Compile a regex pattern to detect lines starting with "Differential Diagnosis:"
DD_RE = re.compile(r"^[^A-z]*Differential Diagnosis")

# Function to clean and remove "Differential Diagnosis" header if present
def clean_service_answer(answer: str) -> str:
    """Remove the 'Differential Diagnosis' header if present, and clean the first line."""
    lines = answer.split("\n")
    # Filter out any line that starts with "Differential Diagnosis:"
    cleaned_lines = [line for line in lines if not DD_RE.match(line)]
    return "\n".join(cleaned_lines)

def split_diagnosis_from_header(answer: str) -> str:
    # Find the position of the identifier
    position = answer.find("1.")
    if position == -1 or position == None:
        return ""
    # Get everything from the identifier onwards
    return answer[position:]

# Clean the diagnosis line by removing leading numbers, periods, asterisks, and spaces
def clean_diagnosis_line(line: str) -> str:
    """Remove leading numbers, asterisks, and unnecessary punctuation/spaces from the diagnosis."""
    line = re.sub(r"^\**\d+\.\s*", "", line)  # Remove leading numbers and periods
    line = line.strip("*")  # Remove asterisks around the text
    return line.strip()  # Strip any remaining spaces


# Split a diagnosis into its main name and synonym if present
def split_diagnosis_and_synonym(diagnosis: str) -> Tuple[str, str]:
    """Split the diagnosis into main name and synonym (if present in parentheses)."""
    match = re.match(r"^(.*)\s*\((.*)\)\s*$", diagnosis)
    if match:
        main_diagnosis, synonym = match.groups()
        return main_diagnosis.strip(), synonym.strip()
    return diagnosis, None  # Return the original diagnosis if no synonym is found