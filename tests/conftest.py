"""
This module contains pytest fixtures and utility functions to set up the test environment,
handle MATLAB engine interactions, and process text files for comparison in unit tests.

Contents:
    Fixtures:
        matlab_engine
        setup_folders
        find_text_file
        extract_section_between_keywords
    Helper_functions:
        process_std_out
        compare_text_blocks
"""

import pytest
import os
import matlab.engine
import shutil
import glob

@pytest.fixture()
def matlab_engine(refactored=True):
    """
    Pytest fixture to start a MATLAB engine session, add a specified directory 
    to the MATLAB path, and clean up after the tests.

    This fixture initializes the MATLAB engine, adds the directory containing 
    MATLAB functions to the MATLAB path, and then yields the engine instance 
    for use in tests. After the tests are done, the MATLAB engine is properly 
    closed.

    Args:
        refactored (bool, optional): If True, use the refactored code path 
            'oneflux_steps/ustar_cp_refactor_wip/'. Defaults to True, using 
            the 'oneflux_steps/ustar_cp_refactor_wip/' path.

    Yields:
        matlab.engine.MatlabEngine: The MATLAB engine instance for running MATLAB 
            functions within tests.

    After the tests complete, the MATLAB engine is closed automatically.
    """
    # Start MATLAB engine
    eng = matlab.engine.start_matlab()

    current_dir = os.getcwd()
    code_path = 'oneflux_steps/ustar_cp_refactor_wip/' if refactored else 'oneflux_steps/ustar_cp'

    # Add the directory containing your MATLAB functions to the MATLAB path
    matlab_function_path = os.path.join(current_dir, code_path)
    eng.addpath(matlab_function_path, nargout=0)

    yield eng

    # Close MATLAB engine after tests are done
    eng.quit()

@pytest.fixture
def setup_folders(tmp_path, testcase: str = "US_ARc"):
    """
    Fixture to set up input and output folders for tests by copying all files 
    from a specified local directory.

    Args:
        tmp_path: A pytest fixture that provides a temporary directory unique to 
                  the test invocation.
        testcase (str): The name of the subdirectory under 'tests/test_artifacts/' 
                        that contains the test files.

    Returns:
        tuple: A tuple containing the paths to the temporary input, the reference output, and 
               the empty output directories as strings.
    """
    # Define paths for the temporary directories
    input_folder = tmp_path / "input"
    reference_output_folder = tmp_path / "ref_output"
    output_folder = tmp_path / "output"

    # Cleanup just in case
    for folder in [input_folder, reference_output_folder, output_folder]:
        if folder.exists():
            shutil.rmtree(folder)

    # Create the output directory (starts empty)
    output_folder.mkdir()

    # Pattern to match directories starting with the `testcase` name
    pattern = os.path.join('tests/test_artifacts', f'{testcase}*')

    # Use glob to find directories that match the pattern
    matching_dirs = glob.glob(pattern)

    # Assuming you want the first matching directory
    if matching_dirs:
        if len(matching_dirs) == 1:
            testcase_path = matching_dirs[0]
        else:
            raise ValueError(f"{pattern}: is not unique")
    else:
        raise FileNotFoundError(f"No matching directory found for pattern: {pattern}")

    data_path= os.path.join(testcase_path, '05_ustar_cp')

    # Copy all files and directories from the testcase input dir to the temporary input folder
    inputs = os.path.join(data_path, 'input')
    if os.path.exists(inputs):
        try:
            shutil.copytree(inputs, str(input_folder), dirs_exist_ok=True)
        except Exception as e:
            print(f"Error during copy: {e}")
    else:
        raise FileNotFoundError(f"Input directory {inputs} does not exist in testcase {testcase}")

    # Copy all files from the testcase ref_output dir to the temporary reference output folder
    ref_outputs = data_path
    if os.path.exists(ref_outputs):
        shutil.copytree(ref_outputs, str(reference_output_folder), dirs_exist_ok=True)
    else:
        raise FileNotFoundError(f"Reference output directory {ref_outputs} does not exist in testcase {testcase}")

    return str(input_folder), str(reference_output_folder), str(output_folder)

@pytest.fixture
def find_text_file():
    """
    Fixture to find the `report` file in the given folder, open it, 
    extract its contents as a list of lines, and return the contents.

    Returns:
        function: A function that takes a folder path and returns the contents 
                  of the first `.txt` file found in that folder as a list of lines.
    """
    def _find_text_file_in_folder(folder):
        # Search for a .txt file in the given folder
        for filename in os.listdir(folder):
            if filename.startswith('report'):
                # Construct the full file path
                file_path = os.path.join(folder, filename)
                
                # Open the file and read its contents as lines
                with open(file_path, 'r', encoding='utf-8') as file:
                    contents = file.readlines()  # Read the file as a list of lines
                return contents
        
        # If no .txt file is found, raise an error
        raise FileNotFoundError(f"No .txt file found in folder: {folder}")

    return _find_text_file_in_folder

@pytest.fixture
def extract_section_between_keywords():
    """
    Fixture to extract a section from a results txt file between two keywords.

    Args:
        data (list): The contents of the file as a list of lines.
        start_keyword (str): The keyword to start extracting from.
        end_keyword (str, optional): The keyword to stop extracting before. 
                                     Defaults to None, which means take all text onward from the start keyword.

    Returns:
        function: A function that takes data (list of lines), start_keyword (str), 
                  and end_keyword (str, optional), and returns the lines between the 
                  start keyword and the end keyword, exclusive of the end keyword.
    """
    def _extract(data, start_keyword, end_keyword=None):
        # Find the index of the first occurrence of the start keyword
        start_idx = -1
        for i, line in enumerate(data):
            if line.strip().startswith(start_keyword):
                start_idx = i
                break  # Stop after finding the first occurrence

        if start_idx == -1:
            raise ValueError(f"No section starting with '{start_keyword}' found in the file")

        # If end_keyword is provided, find its index
        end_idx = len(data)  # Default to end of file if end_keyword is None
        if end_keyword:
            for i, line in enumerate(data[start_idx + 1:], start=start_idx + 1):
                if line.strip().startswith(end_keyword):
                    end_idx = i
                    break  # Stop after finding the first occurrence

        # Extract the section between the start and end keywords
        section = data[start_idx + 1:end_idx]  # Exclusive of both start and end keywords

        return section

    return _extract

def process_std_out(std_out):
    """
    Process standard output from a StringIO object into a list of lines.

    Args:
        std_out (StringIO): The StringIO object containing standard output.

    Returns:
        list: A list of lines from the standard output.
    """
    output = std_out.getvalue()
    output_lines = output.splitlines()
    return output_lines

def compare_text_blocks(text1, text2):
    """
    Compare two blocks of text after stripping whitespace.

    Args:
        text1 (str): The first block of text.
        text2 (str): The second block of text.

    Returns:
        bool: True if the stripped text blocks are identical, False otherwise.
    """
    return text1.replace('\n', '').strip() == text2.replace('\n', '').strip()
