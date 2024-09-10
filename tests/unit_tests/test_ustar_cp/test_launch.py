"""
This module contains unit tests to validate the behavior of the MATLAB `launch` function
under various conditions. The tests ensure that the function handles different scenarios 
correctly, such as missing files, invalid data, and empty input folders. The tests use 
pytest fixtures to set up the necessary test environments and simulate these conditions.
"""

import os
import pytest
from pathlib import Path
import io
from tests.conftest import process_std_out, compare_text_blocks

@pytest.fixture
def setup_test_environment(tmp_path):
    """
    Fixture to set up a test environment with input and output folders populated with 
    dummy data. This fixture creates a temporary input directory with a sample CSV file 
    containing valid data and an empty output directory.

    Args:
        tmp_path (Path): A pytest fixture that provides a unique temporary directory 
                         for the test.

    Returns:
        tuple: A tuple containing the paths to the input and output folders as strings.
    """
    # Create input and output directories
    input_folder = tmp_path / "input"
    output_folder = tmp_path / "output"
    input_folder.mkdir()
    output_folder.mkdir()

    # Create a sample input file in the input directory
    sample_data = """site,ExampleSite
year,2023
lat,51.0
lon,-114.0
timezone,-7
htower,50
timeres,30
Sc_negl,0.5
notes,Sample note
"""
    with open(input_folder / "US-ARc_qca_ustar_2023.csv", "w") as f:
        f.write(sample_data)

    return str(input_folder), str(output_folder)

def test_launch_missing_file(setup_test_environment, matlab_engine, setup_folders):
    """
    Test the MATLAB `launch` function's behavior when the input folder is missing.

    This test simulates a scenario where the input folder is empty or does not contain
    the expected files. The test checks if the MATLAB function returns the expected exit
    code, indicating that it handled the missing file scenario appropriately.

    Args:
        setup_test_environment (fixture): A fixture that sets up input and output folders 
                                          with dummy data for the test.
        matlab_engine (fixture): A fixture that initializes and manages the MATLAB engine session.
        setup_folders (fixture): A fixture that sets up folders for input, reference output, 
                                 and test output.

    Asserts:
        The test asserts that the MATLAB function returns an exit code of 0, indicating 
        that the function identified the missing file scenario, and tests for the std 
        output under this condition.
    """
    _, _, empty_output = setup_folders

    # Run the MATLAB function
    output = io.StringIO()
    exitcode = matlab_engine.launch(empty_output, empty_output, stdout=output)

    # Retrieve the captured output
    output.seek(0)
    output_string = output.readlines()[-2]


    # Check that the exitcode does not indicate an error
    assert exitcode == 0, "Expected zero exitcode for missing file."

    # Check for a specific string in the output
    expected_string = "0 files founded."
    assert compare_text_blocks(expected_string, output_string), f"Expected string '{expected_string}' not found in output."

def test_launch_invalid_data(setup_test_environment, matlab_engine):
    """
    Test the MATLAB `launch` function's behavior with invalid data in the input file.

    This test modifies the content of the input file to contain invalid data and then 
    runs the MATLAB function. It verifies that the function can detect the invalid data 
    and returns the correct exit code.

    Args:
        setup_test_environment (fixture): A fixture that sets up input and output folders 
                                          with dummy data for the test.
        matlab_engine (fixture): A fixture that initializes and manages the MATLAB engine session.

    Asserts:
        The test asserts that the MATLAB function returns a non-zero exit code, indicating 
        that it identified and handled the invalid data correctly.
    """
    input_folder, output_folder = setup_test_environment
    eng = matlab_engine

    # Overwrite the input file with invalid data
    invalid_data = """invalid content"""
    with open(Path(input_folder) / "US-ARc_qca_ustar_2023.csv", "w") as f:
        f.write(invalid_data)

    # Run the MATLAB function
    exitcode = eng.launch(input_folder, output_folder)

    # Check that the exitcode indicates an error
    assert exitcode == 1, "Expected non-zero exitcode for invalid data."

def test_launch_empty_folder(setup_test_environment, matlab_engine):
    """
    Test the MATLAB `launch` function's behavior when the input folder is empty.

    This test simulates an empty input folder scenario by deleting all files in the input 
    folder before running the MATLAB function. It checks whether the function returns the 
    correct exit code, indicating that it detected the empty input folder.

    Args:
        setup_test_environment (fixture): A fixture that sets up input and output folders 
                                          with dummy data for the test.
        matlab_engine (fixture): A fixture that initializes and manages the MATLAB engine session.

    Asserts:
        The test asserts that the MATLAB function returns an exit code of 0, indicating 
        that it correctly identified the empty input folder.
    """
    input_folder, output_folder = setup_test_environment
    eng = matlab_engine

    # Remove all files from the input folder to simulate an empty folder
    for file in Path(input_folder).glob("*"):
        os.remove(file)

    # Run the MATLAB function
    exitcode = eng.launch(input_folder, output_folder)

    # Check that the exitcode indicates an error
    assert exitcode == 0, "Expected zero exitcode for empty input folder."

def test_missing_keywords(setup_test_environment, matlab_engine):
    """
    Test the MATLAB `launch` function's behavior when a keyword is missing from the data
    in the initial lines.

    Args:
        setup_test_environment (fixture): A fixture that sets up input and output folders
                                          with dummy data for the test.
        matlab_engine (fixture): A fixture that initializes and manages the MATLAB engine session.

    Asserts:
        The test asserts that the MATLAB function returns an exit code of 1 with the appropriate
        error message
    """
    input_folder, output_folder = setup_test_environment
    eng = matlab_engine

    # List of sample data fields and values
    sample_data_fields = [("site","US-Arc"),
                    ("year","2006"),
                    ("lat","35.5465"),
                    ("lon","-98.0401"),
                    ("timezone","200601010030,-6"),
                    ("htower","200601010030,4.05"),
                    ("timeres","halfhourly"),
                    ("sc_negl","1"),
                    ("notes","Sample note")]

    # String with 10 newlines
    endbuffer = "bad,bad" * 10

    # Build up successive partial sample files from the above data and
    # try to launch
    partial_sample_data = ""
    for line in sample_data_fields:
        # Write the current partial data to the file
        with open(Path(input_folder) / "US-ARc_qca_ustar_2023.csv", "w") as f:
          f.write(partial_sample_data + endbuffer)

        # Run the MATLAB function
        output = io.StringIO("")
        eng.launch(input_folder, output_folder, stdout=output)

        # Read standard out and get last line
        output.seek(0)
        output_string = output.readlines()[-1]

        assert (output_string == ("processing n.01, US-ARc_qca_ustar_2023.csv..." + line[0] + " keyword not found.\n")), \
                 "Expected error message for missing keyword"

        # Add the current line to the partial data  for the next test
        partial_sample_data += ",".join(line) + "\n"
