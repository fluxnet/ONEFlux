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
   {"x": matlab.double([])
  , "y": matlab.double([])
  , "dx": matlab.double([])
  , "nPerBin": matlab.double([1])
  , "mx": matlab.double([])
  , "my": matlab.double([])
  , "nBins": 0}]

@pytest.mark.parametrize('data', test_data_dx_length_leq_one)
def test_cpdBin_dx_sclar(matlab_engine, data):
    """
    Test cpdBin with scalar dx or empty dx
    """
    nBins, mx, my  = matlab_engine.fcBin(data["x"], data["y"], data["dx"], data["nPerBin"], nargout=3)

    # Check the results
    assert mx == data["mx"]
    assert my == data["my"]
    assert nBins == data["nBins"]