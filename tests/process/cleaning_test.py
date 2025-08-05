from malco.process.cleaning import (
    split_diagnosis_from_header,
    clean_service_answer,
    clean_diagnosis_line,
    split_diagnosis_and_synonym
)

def test_split_diagnosis_from_header_with_header():
    answer = "Differential Diagnosis:\n1. Condition A\n2. Condition B"
    expected = "1. Condition A\n2. Condition B"
    assert split_diagnosis_from_header(answer) == expected

def test_split_diagnosis_from_header_without_header():
    answer = "1. Condition A\n2. Condition B"
    expected = "1. Condition A\n2. Condition B"
    assert split_diagnosis_from_header(answer) == expected

def test_split_diagnosis_from_header_no_diagnosis():
    answer = "Differential Diagnosis:\nNo conditions listed"
    expected = ""
    assert split_diagnosis_from_header(answer) == expected

def test_split_diagnosis_from_header_empty_string():
    answer = ""
    expected = ""
    assert split_diagnosis_from_header(answer) == expected

def test_split_diagnosis_from_header_no_numbered_list():
    answer = "Differential Diagnosis:\nCondition A\nCondition B"
    expected = ""


def test_split_diagnosis_from_header_with_header():
    answer = "Differential Diagnosis:\n1. Condition A\n2. Condition B"
    expected = "1. Condition A\n2. Condition B"
    assert split_diagnosis_from_header(answer) == expected

def test_split_diagnosis_from_header_without_header():
    answer = "1. Condition A\n2. Condition B"
    expected = "1. Condition A\n2. Condition B"
    assert split_diagnosis_from_header(answer) == expected

def test_split_diagnosis_from_header_no_diagnosis():
    answer = "Differential Diagnosis:\nNo conditions listed"
    expected = ""
    assert split_diagnosis_from_header(answer) == expected

def test_split_diagnosis_from_header_empty_string():
    answer = ""
    expected = ""
    assert split_diagnosis_from_header(answer) == expected

def test_split_diagnosis_from_header_no_numbered_list():
    answer = "Differential Diagnosis:\nCondition A\nCondition B"
    expected = ""
    assert split_diagnosis_from_header(answer) == expected

def test_clean_service_answer_with_header():
    answer = "Differential Diagnosis:\n1. Condition A\n2. Condition B"
    expected = "1. Condition A\n2. Condition B"
    assert clean_service_answer(answer) == expected

def test_clean_service_answer_without_header():
    answer = "1. Condition A\n2. Condition B"
    expected = "1. Condition A\n2. Condition B"
    assert clean_service_answer(answer) == expected

def test_clean_service_answer_empty_string():
    answer = ""
    expected = ""
    assert clean_service_answer(answer) == expected

def test_clean_diagnosis_line_with_numbers():

    line = "1. Condition A"
    expected = "Condition A"
    assert clean_diagnosis_line(line) == expected

def test_clean_diagnosis_line_with_asterisks():
    line = "*1. Condition A*"
    expected = "Condition A"
    assert clean_diagnosis_line(line) == expected

def test_clean_diagnosis_line_without_numbers():
    line = "Condition A"
    expected = "Condition A"
    assert clean_diagnosis_line(line) == expected

def test_clean_diagnosis_line_empty_string():
    line = ""
    expected = ""
    assert clean_diagnosis_line(line) == expected

def test_split_diagnosis_and_synonym_with_synonym():
    diagnosis = "Condition A (Synonym A)"
    expected = ("Condition A", "Synonym A")
    assert split_diagnosis_and_synonym(diagnosis) == expected

def test_split_diagnosis_and_synonym_without_synonym():
    diagnosis = "Condition A"
    expected = ("Condition A", None)
    assert split_diagnosis_and_synonym(diagnosis) == expected

def test_split_diagnosis_and_synonym_empty_string():
    diagnosis = ""
    expected = ("", None)
    assert split_diagnosis_and_synonym(diagnosis) == expected
