"""
This module contains unit tests to validate the behavior of the MATLAB `launch` function
under various conditions. The tests ensure that the function handles different scenarios 
correctly, such as missing files, invalid data, and empty input folders. The tests use 
pytest fixtures to set up the necessary test environments and simulate these conditions.
"""

import os
import pytest
from pathlib import Path

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
        that the function identified the missing file scenario.
    """
    _, _, empty_output = setup_folders

    # Run the MATLAB function
    out = io.StringIO()
    exitcode = matlab_engine.launch(empty_output, empty_output)

    # Retrieve the captured output
    captured_output = out.getvalue()

    # Check that the exitcode does not indicate an error
    assert exitcode == 0, "Expected zero exitcode for missing file."

    # Check for a specific string in the output
    expected_string = "0 files founded."
    assert expected_string in captured_output, f"Expected string '{expected_string}' not found in output."

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

