# conftest.py

import matlab.engine
import pytest
import os

@pytest.fixture(scope="module")
def matlab_engine():
    # Start MATLAB engine
    eng = matlab.engine.start_matlab()

    # Add the directory containing your MATLAB functions to the MATLAB path
    matlab_function_path = os.path.abspath('matlab_functions')  # Adjust this path to where your MATLAB files are located
    eng.addpath(matlab_function_path, nargout=0)

    yield eng

    # Close MATLAB engine after tests are done
    eng.quit()
