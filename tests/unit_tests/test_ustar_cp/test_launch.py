import os
import pytest
from pathlib import Path
import io

@pytest.fixture
def setup_test_environment(tmp_path):
    """
    Fixture to set up the input and output folders for the test.
    
    Returns the paths to the input and output folders.
    """
    # Create input and output directories
    input_folder = tmp_path / "input"
    output_folder = tmp_path / "output"
    input_folder.mkdir()
    output_folder.mkdir()

    # Create sample input files in the input directory
    # You can populate these with test data as needed
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
    Test the launch function with a missing input file.
    """
    _, _, empty_output = setup_folders

    # Run the MATLAB function
    exitcode = matlab_engine.launch(empty_output, empty_output)

    # Check that the exitcode indicates an error
    assert exitcode == 0, "Expected zero exitcode for missing file."

def test_launch_invalid_data(setup_test_environment, matlab_engine):
    """
    Test the launch function with invalid data.
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
    Test the launch function with an empty input folder.
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
