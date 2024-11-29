# Contains tests for testing the cpdBin function
# which calculates the binned mean values of two vectors
# (given as the first two parameters) with control
# over the binning technique as the third parameter
# and the number per bin as the fourth parameter.

import pytest
import numpy as np
from tests.conftest import process_std_out, compare_text_blocks
import matlab.engine

# Test fixtures for an empty or scalar dx
test_data_dx_length_leq_one = [
  # Case with empty dx
   {"x": []
  , "y": []
  , "dx": []
  , "nPerBin": [1]
  , "mx": []
  , "my": []
  , "nBins": 0},
  # Case with scalar dx and simple binning
   {"x": [1.0, 2.0, 3.0]
  , "y": [1.0, 2.0, 3.0]
  , "dx": [1.0]
  , "nPerBin": [1]
  , "mx": [[1.0],[2.0],[3.0]]
  , "my": [[1.0],[2.0],[3.0]]
  , "nBins": 3}]

def reverse(x):
  return x.T[::-1]

@pytest.mark.parametrize('data', test_data_dx_length_leq_one)
def test_cpdBin_dx_sclar(matlab_engine, data):
    """
    Test cpdBin with scalar dx or empty dx
    """
    # Apply the test case
    nBins, mx, my  = matlab_engine.fcBin(np.asarray(data["x"]), np.asarray(data["y"]), np.asarray(data["dx"]), np.asarray(data["nPerBin"]), nargout=3)
    # Check the results
    assert mx == matlab.double(data["mx"])
    assert my == matlab.double(data["my"])
    assert nBins == data["nBins"]

    # Apply the test case but reversing one set of data
    nBins, mx, my  = matlab_engine.fcBin(np.asarray(data["x"][::-1]), np.asarray(data["y"]), np.asarray(data["dx"]), np.asarray(data["nPerBin"]), nargout=3)
    # Check the results
    assert mx == matlab.double(data["mx"])
    assert my == matlab.double(data["my"][::-1])
    assert nBins == data["nBins"]