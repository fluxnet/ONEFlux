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
import filecmp

"""
  Chosen test cases (identified by their site code; first 5 characters) to give adequate coverage (with data files in `tests/test_artifacts`)
    CA-Cbo, US-ARM, US-Ne1, US-Syv, US-Vcm
  Additional test case:
    US_ARc_sample: Listed on Github as reference test case
  Analysis of supplied test cases:
    Error report types (reported against at least one case in case report file):
      Type A: "Too few selected change points:"
      Type B: "Function cpdBin aborted. dx cannot be <=0"
      Type C: "(PPFD_IN from SW_IN)...NEE is empty!"
      Type D: "NEE is empty!"
      Type E: "Less than 10% successful detections."
      Type F: "column SW_IN not found!"
      Type G: "(PPFD_IN from SW_IN)...ok"
      Type H: "(PPFD_IN from SW_IN)...Too few selected change points"
    Analysis case summary:
      CA-Cbo: A,  C
      US-ARM: A,  E
      US_NE1: A,  G,  H
      US_Syv: A,  D,  F
      US_Vcm: A,  B,  H
    """

test_cases = [
    ("US_ARc", [1]),("CA-Cbo", [1]), ("US-ARM", [1]), ("US-Ne1",[1]), ("US-Syv", [1]),("US-Vcm", [1])
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
    7. Assert ref and test output fodlers conatin the same files.
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

    # Step 7: Assert that the reference output folder and test run output contain the same files
    comparison = filecmp.dircmp(ref_outputs, test_outputs)
    assert comparison, f"Expected test and reference output folders have same contents, but comparison test fails"



   
