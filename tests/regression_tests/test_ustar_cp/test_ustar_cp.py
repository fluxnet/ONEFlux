"""
This module contains regression tests to validate the MATLAB uStar CP processing function.
The tests compare the output generated by the MATLAB function against pre-defined expected 
outputs, ensuring that the function behaves as intended across various scenarios.

The tests are parameterized to allow easy addition of new test cases and to automate the 
comparison of MATLAB's output with expected results. The focus is on validating the standard 
output and the exit code returned by the MATLAB function.
"""

import pytest
import io

test_cases = [
    ("US_ARc_sample", [1]),
    # Add more test cases with their respective expected values
    # Expected values format: [exitvalue]
]

@pytest.mark.parametrize("testcase, expected_values", test_cases)
def test_ustar_cp(testcase, expected_values, setup_folders, matlab_engine, find_text_file, extract_section_between_keywords):
    """
    Validate MATLAB's uStar CP processing function output against expected results.

    This regression test ensures that the MATLAB function `launch` correctly processes uStar data
    and produces the expected output. The function's standard output (`stdout`) is captured and 
    compared with a reference output stored in a predefined text file. The test also checks that 
    the function returns the expected exit code.

    Parameters:
    - testcase: The specific test case being executed, as defined in the test parameters.
    - expected_values: A list containing expected results, where the first value is the expected 
      exit code returned by the MATLAB function.
    - setup_folders: A fixture that sets up the input, reference output, and test output folders 
      required for the test.
    - matlab_engine: A fixture that initializes the MATLAB engine session and adds the necessary 
      directory to the MATLAB path.
    - find_text_file: A fixture that retrieves the content of the first `.txt` file found in a 
      specified folder.
    - extract_section_between_keywords: A fixture that extracts a section of text between two 
      specified keywords from a given list of lines.

    Test Steps:
    1. Setup the necessary folders (input, reference output, and test output) using the setup_folders fixture.
    2. Run the MATLAB function `launch` with the provided input and output paths, capturing its `stdout` and `stderr`.
    3. Extract the expected output section from the reference text file using the `find_text_file` and 
       `extract_section_between_keywords` fixtures.
    4. Extract the corresponding output section from the captured MATLAB `stdout`.
    5. Compare the processed MATLAB output with the expected output.
    6. Assert that the MATLAB function returns the expected exit code.
    """

    # Step 1: Setup input, reference output, and test output folders using the provided fixture
    inputs, ref_outputs, test_outputs = setup_folders

    # Step 2: Capture stdout and stderr from the MATLAB engine during the function execution
    out = io.StringIO()
    err = io.StringIO()
    exitcode = matlab_engine.launch(inputs, test_outputs, stdout=out, stderr=err)

    # Step 3: Retrieve the expected output from the reference text file and extract the relevant section
    ref_text = find_text_file(ref_outputs)
    expected_output_lines = extract_section_between_keywords(ref_text, 'processing')
    expected_output = ''.join(expected_output_lines).strip()

    # Step 4: Ensure captured output is flushed to the buffer and convert it into a list of lines
    out_value = out.getvalue()
    out_value_lines = out_value.splitlines()

    # Extract and process the relevant processing section from the captured output
    test_output_lines = extract_section_between_keywords(out_value_lines, 'processing')
    test_output = '\n'.join(test_output_lines).strip()

    # Step 5: Assert that the expected processing block matches the captured stdout from MATLAB
    assert expected_output == test_output, "The expected text block does not match the MATLAB output."

    # Step 6: Assert that the MATLAB function returns the expected exit code
    assert exitcode == expected_values[0], f"Expected exit code {expected_values[0]}, but got {exitcode}."





   