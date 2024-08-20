import pytest
import os
import matlab.engine
import shutil

@pytest.fixture()
def matlab_engine(refactored = False):
    """
    Pytest fixture to start a MATLAB engine session, add a specified directory 
    to the MATLAB path, and clean up after the tests.

    This fixture initializes the MATLAB engine, adds the directory containing 
    MATLAB functions to the MATLAB path, and then yields the engine instance 
    for use in tests. After the tests are done, the MATLAB engine is properly 
    closed.

    Args:
        refactored (bool, optional): If True, use the refactored code path 
            'oneflux_steps/ustar_cp_refactor_wip/'. Defaults to False, using 
            the 'oneflux_steps/ustar_cp/' path.

    Yields:
        matlab.engine.MatlabEngine: The MATLAB engine instance for running MATLAB 
            functions within tests.

    After the tests complete, the MATLAB engine is closed automatically.
    """

    # Start MATLAB engine
    eng = matlab.engine.start_matlab()

    current_dir = os.getcwd()
    code_path = None
    if refactored:
        code_path = 'oneflux_steps/ustar_cp_refactor_wip/'
    else:
        code_path = 'oneflux_steps/ustar_cp'

    # Add the directory containing your MATLAB functions to the MATLAB path
    matlab_function_path = os.path.join(current_dir, code_path) # Adjust this path to where your MATLAB files are located
    eng.addpath(matlab_function_path, nargout=0)

    yield eng

    # Close MATLAB engine after tests are done
    eng.quit()

@pytest.fixture
def setup_folders(tmpdir, testcase):
    """
    Fixture to set up input and output folders for tests by copying all files 
    from a specified local directory.

    Args:
        tmpdir: A pytest fixture that provides a temporary directory unique to 
                the test invocation.
        testcase (str): The name of the subdirectory under 'tests/test_fixtures/local_directory' 
                        that contains the test files.

    Returns:
        tuple: A tuple containing the paths to the temporary input and output 
               directories as strings.
    """
    # Define paths for the temporary directories
    input_folder = tmpdir.mkdir("input")
    output_folder = tmpdir.mkdir("output")

    # Path to the local directory containing files to be copied
    testcase_path = os.path.join('tests/test_fixtures/local_directory', testcase)

    # Ensure the local directory exists
    if not os.path.exists(testcase_path):
        raise FileNotFoundError(f"Local directory {testcase_path} does not exist")

    # Copy all files and directories from the testcase input dir to the temporary input folder
    inputs = os.path.join(testcase_path, 'input')
    shutil.copytree(inputs, str(input_folder))
    
    # Copy all files and directories from the testcase dir to the temporary output folder
    shutil.copytree(testcase_path, str(output_folder))

    return str(input_folder), str(output_folder)
