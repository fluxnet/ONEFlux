import pytest
import os
import matlab.engine
import shutil

@pytest.fixture()
def matlab_engine(refactored = False):
    # Start MATLAB engine
    eng = matlab.engine.start_matlab()

    current_dir = os.getcwd()
    code_path = 'oneflux_steps/ustar_cp/'
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
    """Fixture to setup input and output folders for tests by copying all files from a specified local directory."""
    # Define paths for the temporary directories
    input_folder = tmpdir.mkdir("input")
    output_folder = tmpdir.mkdir("output")

    # Path to the local directory containing files to be copied
    testcase_path = os.join.path('tests/test_fixtures/local_directory', testcase)

    # Ensure the local directory exists
    if not os.path.exists(testcase_path):
        raise FileNotFoundError(f"Local directory {testcase_path} does not exist")

    def copy_tree(src, dst):
        """Recursively copy files and directories from src to dst."""
        if os.path.isdir(src):
            os.makedirs(dst, exist_ok=True)
            for item in os.listdir(src):
                s = os.path.join(src, item)
                d = os.path.join(dst, item)
                copy_tree(s, d)
        else:
            shutil.copy2(src, dst)

    # Copy all files and directories from the testcase input dir to the temporary input folder
    inputs = os.join.path(testcase_path, 'input')
    copy_tree(inputs, input_folder)
    # Copy all files and directories from the testcase dir to the temporary output folder
    copy_tree(testcase_path, output_folder)

    return str(input_folder), str(output_folder)
