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
import numpy as np
import pandas as pd
import matlab.engine

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

def assert_csv_files_equal(file1, file2):
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)

    # This assertion will pass if the DataFrames are identical
    assert df1.equals(df2), f"CSV files {file1} and {file2} do not match."

def test_launch_missing_file(setup_test_environment, test_engine, setup_folders):
    """
    Test the MATLAB `launch` function's behavior when the input folder is missing.

    This test simulates a scenario where the input folder is empty or does not contain
    the expected files. The test checks if the MATLAB function returns the expected exit
    code, indicating that it handled the missing file scenario appropriately.

    Args:
        setup_test_environment (fixture): A fixture that sets up input and output folders
                                          with dummy data for the test.
        test_engine (fixture): A fixture that initializes and manages the MATLAB engine session.
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
    exitcode = test_engine.launch(empty_output, empty_output, stdout=output)

    # Retrieve the captured output
    output.seek(0)
    output_string = output.readlines()[-2]


    # Check that the exitcode does not indicate an error
    assert exitcode == 0, "Expected zero exitcode for missing file."

    # Check for a specific string in the output
    expected_string = "0 files founded."
    assert compare_text_blocks(expected_string, output_string), f"Expected string '{expected_string}' not found in output."

def test_launch_invalid_data(setup_test_environment, test_engine):
    """
    Test the MATLAB `launch` function's behavior with invalid data in the input file.

    This test modifies the content of the input file to contain invalid data and then
    runs the MATLAB function. It verifies that the function can detect the invalid data
    and returns the correct exit code.

    Args:
        setup_test_environment (fixture): A fixture that sets up input and output folders
                                          with dummy data for the test.
        test_engine (fixture): A fixture that initializes and manages the MATLAB engine session.

    Asserts:
        The test asserts that the MATLAB function returns a non-zero exit code, indicating
        that it identified and handled the invalid data correctly.
    """
    input_folder, output_folder = setup_test_environment
    
    # Overwrite the input file with invalid data
    invalid_data = """invalid content"""
    with open(Path(input_folder) / "US-ARc_qca_ustar_2023.csv", "w") as f:
        f.write(invalid_data)

    # Run the MATLAB function
    exitcode = test_engine.launch(input_folder, output_folder)

    # Check that the exitcode indicates an error
    assert exitcode == 1, "Expected non-zero exitcode for invalid data."

def test_launch_empty_folder(setup_test_environment, test_engine):
    """
    Test the MATLAB `launch` function's behavior when the input folder is empty.

    This test simulates an empty input folder scenario by deleting all files in the input
    folder before running the MATLAB function. It checks whether the function returns the
    correct exit code, indicating that it detected the empty input folder.

    Args:
        setup_test_environment (fixture): A fixture that sets up input and output folders
                                          with dummy data for the test.
        test_engine (fixture): A fixture that initializes and manages the MATLAB engine session.

    Asserts:
        The test asserts that the MATLAB function returns an exit code of 0, indicating
        that it correctly identified the empty input folder.
    """
    input_folder, output_folder = setup_test_environment

    # Remove all files from the input folder to simulate an empty folder
    for file in Path(input_folder).glob("*"):
        os.remove(file)

    # Run the MATLAB function
    exitcode = test_engine.launch(input_folder, output_folder)

    # Check that the exitcode indicates an error
    assert exitcode == 0, "Expected zero exitcode for empty input folder."

def test_missing_keywords(setup_test_environment, test_engine):
    """
    Test the MATLAB `launch` function's behavior when a keyword is missing from the data
    in the initial lines.

    Args:
        setup_test_environment (fixture): A fixture that sets up input and output folders
                                          with dummy data for the test.
        test_engine (fixture): A fixture that initializes and manages the MATLAB engine session.

    Asserts:
        The test asserts that the MATLAB function returns an exit code of 1 with the appropriate
        error message
    """
    input_folder, output_folder = setup_test_environment
    eng = test_engine

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


loadData_test_cases = ['2005', '2006']
@pytest.mark.parametrize('year', loadData_test_cases)
def test_loadData(year, setup_folders, test_engine):
    """
    Test the MATLAB `loadData` function with valid input files.

    Checks if the header, data, and column index files are correctly extracted or generated from the input file.

    Args:
    - year: The year of the data file to be tested.
    - setup_folders: A fixture that sets up the input, reference output, and test output folders required for the test.
    - test_engine: A fixture that initializes the MATLAB engine session and adds the necessary directory to the MATLAB path.
    Asserts:
    - The test asserts that the header, data, and column index files generated by the MATLAB function match the expected output.
    """
    # Setup the input and output folders
    input_folder, reference_output_folder, output_folder = setup_folders
    input_folder = input_folder + '/'
    output_folder = output_folder + '/'

    # Call the MATLAB function, passing the temporary directory path

    filename = f'US-ARc_qca_ustar_{year}.csv'
    notes_file = f'tests/test_artifacts/launch_artifacts/loadData_input_notes_US-ARc_qca_ustar_{year}.csv'
    notes = list(pd.read_csv(notes_file, header=None))
    input_columns_names = ['USTAR', 'NEE', 'TA', 'PPFD_IN' ,'SW_IN']

    test_engine.loadData(input_folder, filename, notes, input_columns_names, output_folder, nargout=0)

    assert_csv_files_equal(f"tests/test_artifacts/launch_artifacts/loadData_output_header_US-ARc_qca_ustar_{year}.csv", output_folder + "header.csv")
    assert_csv_files_equal(f"tests/test_artifacts/launch_artifacts/loadData_output_data_US-ARc_qca_ustar_{year}.csv", output_folder + "data.csv")
    assert_csv_files_equal(f"tests/test_artifacts/launch_artifacts/loadData_output_columns_index_US-ARc_qca_ustar_{year}.csv", output_folder + "columns_index.csv")


mapColumnNamesToIndices_test_cases = [(['USTAR', 'NEE', 'TA', 'PPFD_IN' ,'SW_IN'], [-1,-1,-1,-1,-1], [5,3,4,7,6], 0),
                                      ( ['USTAR', 'NEE', 'NEE', 'PPFD_IN' ,'SW_IN'], [-1,-1,-1,-1,-1], [5,3,3,7,6], 0),
                                      ( ['USTAR', 'NEE', 'TA', 'PPFD_IN' ,'SW_IN'], [100,-1,-1,-1,-1], [100,3,4,-1,-1], 1)
]
@pytest.mark.parametrize('input_columns_names, columns_index, expected_columns_index, expected_exitcode', mapColumnNamesToIndices_test_cases)
def test_mapColumnNamesToIndices(test_engine, input_columns_names, columns_index, expected_columns_index, expected_exitcode):
    """
    Test the MATLAB `mapColumnNamesToIndices` function maps the column names to their respective indices.

    Args:
    - test_engine: A fixture that initializes the MATLAB engine session and adds the necessary directory to the MATLAB path.
    Asserts:
    Nominal case:
    - Asserts that the column indices generated by the MATLAB function maps the column names to their respective indices.
    - Asserts that if column index is already set, the function exits with a non-zero exit code

    """

    # Read the input files
    header = []
    header_file = 'tests/test_artifacts/launch_artifacts/mapColumnNamesToIndices_input_header_US-ARc_qca_ustar_2005.csv'
    notes = list(pd.read_csv('tests/test_artifacts/launch_artifacts/mapColumnNamesToIndices_input_notes_US-ARc_qca_ustar_2005.csv'))
    columns_index = matlab.int8(vector=columns_index, is_complex=False)

    # Call the MATLAB function
    exitcode, output_columns_index = test_engine.mapColumnNamesToIndices(header, input_columns_names, notes, columns_index, header_file, nargout=2)

    assert output_columns_index.tomemoryview().tolist()[0] == expected_columns_index
    assert exitcode == expected_exitcode, f"Expected {expected_exitcode} exitcode for mapColumnNamesToIndices"


@pytest.mark.parametrize('columns_index, expected_ppfd_from_rg, expected_exitcode', [([5,3,4,7,6], 0, 0), ([-1,3,4,7,6], 0, 1), ([5,3,4,-1,6], 1, 0)])
def test_ppfdColExists(test_engine, columns_index, expected_ppfd_from_rg, expected_exitcode):
    """
    Test the MATLAB `ppfdColExists` function checks if the PPFD column exists in the data.

    Args:
    - test_engine: A fixture that initializes the MATLAB engine session and adds the necessary directory to the MATLAB path.
    - columns_index: A list of column indices.
    - expected_ppfd_from_rg: The expected value for the PPFD from RG flag to decide if PPFD is derived from RG.
    - expected_exitcode: The expected exit code returned by the MATLAB function.
    Asserts:
    - Asserts that if the PPFD column exists, the function returns the correct PPFD from RG flag and exit code.
    - Asserts that if the PPFD column does not exist, the function returns the correct PPFD from RG flag and exit code.
    - Asserts that if a column index is not set, the function exits with a non-zero exit code.
    """

    # Create the input data
    ppfd_index = 4
    columns_index = matlab.int8(vector=columns_index, is_complex=False)
    input_columns_names = ['USTAR', 'NEE', 'TA', 'PPFD_IN' ,'SW_IN']

    # Call the MATLAB function
    ppfd_from_rg, exitcode = test_engine.ppfdColExists(ppfd_index, columns_index, input_columns_names, nargout=2)

    assert ppfd_from_rg == expected_ppfd_from_rg, f"Expected {expected_ppfd_from_rg} for ppfd_from_rg"
    assert exitcode == expected_exitcode, f"Expected {expected_exitcode} exitcode for ppfdColExists"


@pytest.mark.parametrize("year_and_type, expected_ppfd_from_rg", [('2005',0), ('2005_nan', 1)])
def test_areAllPpfdValuesInvalid(test_engine, year_and_type, expected_ppfd_from_rg):
    """
    Test the MATLAB `areAllPpfdValuesInvalid` function checks if all PPFD values are invalid.
    Args:
    - test_engine: A fixture that initializes the MATLAB engine session and adds the necessary directory to the MATLAB path.
    - year_and_type: The year and type of the data file to be tested.
    - expected_ppfd_from_rg: The expected value for the PPFD from RG flag to decide if PPFD is derived from RG.
    Asserts:
    - Asserts that if all PPFD values are invalid, the function returns the correct, PPFD value and PPFD from RG flag.
    - Asserts that if all PPFD values are not invalid, the function returns the correct PPFD value and PPFD from RG flag.
    """

    # Create the input data
    ppfd_from_rg = 0
    columns_index = matlab.int8(vector=[5,3,4,7,6], is_complex=False)
    ppfd_index = 4
    data = []

    # Read the input and output files
    site_data_file = f'tests/test_artifacts/launch_artifacts/areAllPpfdValuesInvalid_input_data_US-ARc_qca_ustar_{year_and_type}.csv'

    expected_ppfd = pd.read_csv(f'tests/test_artifacts/launch_artifacts/areAllPpfdValuesInvalid_output_PPFD_US-ARc_qca_ustar_{year_and_type}.csv', header=None)
    expected_ppfd = expected_ppfd.iloc[:,0].to_numpy()

    # Call the MATLAB function
    output_ppfd, output_ppfd_from_rg = test_engine.areAllPpfdValuesInvalid(ppfd_from_rg, columns_index, ppfd_index, data, site_data_file, nargout=2)

    # Convert the MATLAB output to a numpy array
    output_ppfd = output_ppfd.tomemoryview().tolist()
    output_ppfd = np.array(output_ppfd).flatten()

    assert np.allclose(output_ppfd, expected_ppfd), "output_ppfd and expected_ppfd do not match"
    assert output_ppfd_from_rg == expected_ppfd_from_rg


@pytest.mark.parametrize("year", ['2005', '2006'])
def test_derivePpfdColFromRg(test_engine, year):
    """
    test the MATLAB `derivePpfdColFromRg` function derives the PPFD column from the RG column.
    Args:
    - test_engine: A fixture that initializes the MATLAB engine session and adds the necessary directory to the MATLAB path.
    - year: The year of the data file to be tested.
    Asserts:
    - Asserts that the PPFD column derived from the RG column matches the expected output.
    """

    # Read the input and output files
    rg = pd.read_csv(f'tests/test_artifacts/launch_artifacts/derivePpfdColFromRg_input_Rg_US-ARc_qca_ustar_{year}.csv', header=None)
    rg = rg.iloc[:,0].to_numpy()
    rg = matlab.double(rg.tolist())
    expected_ppfd = pd.read_csv(f'tests/test_artifacts/launch_artifacts/derivePpfdColFromRg_output_PPFD_US-ARc_qca_ustar_{year}.csv', header=None)
    expected_ppfd = expected_ppfd.iloc[:,0].to_numpy()

    # Call the MATLAB function
    output_ppfd = test_engine.derivePpfdColFromRg(rg, nargout=1)

    # Convert the MATLAB output to a numpy array
    output_ppfd = output_ppfd.tomemoryview().tolist()
    output_ppfd = np.array(output_ppfd).flatten()

    assert np.allclose(output_ppfd, expected_ppfd), "output_ppfd and expected_ppfd do not match"

@pytest.mark.parametrize("year", ['2005', '2006'])
def test_setMissingDataNan(test_engine, year):
    """
    Test the MATLAB `setMissingDataNan` function sets missing data to NaN.
    Args:
    - test_engine: A fixture that initializes the MATLAB engine session and adds the necessary directory to the MATLAB path.
    - year: The year of the data file to be tested.
    Asserts:
    - Asserts that the missing data is set to NaN in the output columns.
    """

    site_columns_names = ['uStar', 'NEE', 'Ta', 'PPFD', 'Rg']

    # Create a dictionary to store the site columns
    site_columns = {key: None for key in site_columns_names}
    expected_output = {key: None for key in site_columns_names}

    # Read and convert the input columns to MATLAB double
    for col in site_columns:
        column = pd.read_csv(f'tests/test_artifacts/launch_artifacts/setMissingDataNan_input_{col}_US-ARc_qca_ustar_{year}.csv', header=None).iloc[:,0].to_numpy()
        site_columns[col] = matlab.double(column.tolist())

    # Call the MATLAB function
    output_ustar, output_nee, output_ta, output_ppfd, output_rg = \
    test_engine.setMissingDataNan(site_columns['uStar'], site_columns['NEE'], site_columns['Ta'], site_columns['PPFD'], site_columns['Rg'], nargout=5)

    # Read and convert the expected output columns to MATLAB double
    for col in expected_output:
        column = pd.read_csv(f'tests/test_artifacts/launch_artifacts/setMissingDataNan_output_{col}_US-ARc_qca_ustar_{year}.csv', header=None).iloc[:,0].to_numpy()
        expected_output[col] = matlab.double(column.tolist())

    assert np.allclose(output_ustar, expected_output['uStar'], equal_nan=True), "output_ustar and expected_ustar do not match"
    assert np.allclose(output_nee, expected_output['NEE'], equal_nan=True), "output_nee and expected_nee do not match"
    assert np.allclose(output_ta, expected_output['Ta'], equal_nan=True), "output_ta and expected_ta do not match"
    assert np.allclose(output_ppfd, expected_output['PPFD'], equal_nan=True), "output_ppfd and expected_ppfd do not match"
    assert np.allclose(output_rg, expected_output['Rg'], equal_nan=True), "output_rg and expected_rg do not match"


@pytest.mark.parametrize("year, expected_exitcode", [('2005', 0), ('2006', 0), ('2005_nan', 1)])
def test_anyColumnsEmpty(test_engine, year, expected_exitcode):
    site_columns_names = ['uStar', 'NEE', 'Ta', 'Rg']
    site_columns = {key: None for key in site_columns_names}

    # Read and convert the input columns to MATLAB double
    for col in site_columns:
        column = pd.read_csv(f'tests/test_artifacts/launch_artifacts/anyColumnsEmpty_input_{col}_US-ARc_qca_ustar_{year}.csv', header=None).iloc[:,0].to_numpy()
        site_columns[col] = matlab.double(column.tolist())

    # Call the MATLAB function
    exitcode = test_engine.anyColumnsEmpty(site_columns['uStar'], site_columns['NEE'], site_columns['Ta'], site_columns['Rg'], nargout=1)

    assert exitcode == expected_exitcode, f"Expected {expected_exitcode} exitcode for anyColumnsEmpty"


@pytest.mark.parametrize("year", ['2005', '2006'])
def test_createTimeArray(test_engine, year):

    # Read the input file
    ustar = pd.read_csv(f'tests/test_artifacts/launch_artifacts/createTimeArray_input_uStar_US-ARc_qca_ustar_{year}.csv', header=None).iloc[:,0].to_numpy()
    ustar = matlab.double(ustar.tolist())

    # Call the MATLAB function
    output_t = test_engine.createTimeArray(ustar, nargout=1)

    # Convert the MATLAB output to a numpy array
    output_t = output_t.tomemoryview().tolist()
    output_t = np.array(output_t).flatten()

    # Read the expected output file
    expected_t = pd.read_csv(f'tests/test_artifacts/launch_artifacts/createTimeArray_output_t_US-ARc_qca_ustar_{year}.csv', header=None).iloc[:,0].to_numpy()

    assert np.allclose(output_t, expected_t), "output_t and expected_t do not match"

