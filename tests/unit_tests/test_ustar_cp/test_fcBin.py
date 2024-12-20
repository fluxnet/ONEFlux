# Contains tests for testing the cpdBin function
# which calculates the binned mean values of two vectors
# (given as the first two parameters) with control
# over the binning technique as the third parameter
# and the number per bin as the fourth parameter.

import pytest
import numpy as np
import pandas as pd
import matlab.engine
from tests.conftest import compare_matlab_arrays, to_matlab_type, process_std_out, compare_text_blocks

from hypothesis import given, settings, HealthCheck
from hypothesis.strategies import floats, lists, integers
import os

# Hypothesis tests for fcBin
@given(data=lists(floats(allow_nan=True, allow_infinity=False), min_size=2),
       scale=floats(allow_infinity=False),
       translate=floats(allow_infinity=False))
@settings(deadline=1000)
def test_singleton_bins_1D_data(data, scale, translate, test_engine):
    """
    Tests the behaviour of `fcBin` for binning based on discrete bins of size 1
    for one dimemsional data"""

    # Use the initial data to generate two vectors worth of data
    # based on some scaling and translation to get data2
    data1 = data
    data2 = [scale * item + translate for item in data]

    # Use `fcBin`
    nBins, mx, my  = test_engine.fcBin(to_matlab_type(data1), to_matlab_type(data2),
                                         to_matlab_type([]), 1.0, nargout=3)

    # Number of bins is the length of the data
    # minus the number of NaNs in combined data
    datacomb =[data1[i] + data2[i] for i in range(len(data1))]
    assert nBins == (len(data1) - sum([np.isnan(item) for item in datacomb]))

    # Helper routine to check results
    def check(ys, data):
      # If the result was a singleton float, it should be in the original data
      if type(ys) == float:
        assert np.any([np.isclose(ys, item, equal_nan=True) for item in data])
      else:
        for bin in ys:
          # every bin is of size 1
          assert len(bin) == 1
          # every element of the bin came originally from data
          # unless it is `inf` which seems a corner case in `fcBin` not considered
          if not(np.isinf(bin[0])):
            assert np.any([np.isclose(bin[0], item, equal_nan=True) for item in data])

    check(mx, data1)
    check(my, data2)

@given(data=lists(floats(allow_nan=True, allow_infinity=False), min_size=2),
       scale=floats(allow_infinity=False,allow_nan=False),
       translate=floats(allow_infinity=False,allow_nan=False),
       row=integers(min_value=1, max_value=4))
@settings(deadline=1000)
def test_singleton_bins_2D_data(data, scale, row, translate, test_engine):
    """
    Tests the behaviour of `fcBin` for binning based on discrete bins of size 1
    for two-dimesional data"""

    # Pad data to be a multiple of `row`
    data = data + [np.nan] * (row - len(data) % row)
    # Turn data into a 2D array with row length given by `row`
    data = np.array(data).reshape(-1, row)

    # Use the initial data to generate two vectors worth of data
    # based on some scaling and translation to get data2
    data1 = data
    data2 = [[scale * item + translate for item in row] for row in data]

    # Use `fcBin`
    nBins, mx, my  = test_engine.fcBin(matlab.double(data1), matlab.double(data2),
                                         to_matlab_type([]), 1.0, nargout=3)

    # Number of bins is the length of the data
    # minus the number of NaNs in combined data
    datacomb =[data1[i][j] + data2[i][j] for j in range(row) for i in range(len(data1))]
    assert nBins == (len(datacomb) - sum([np.isnan(item) for item in datacomb]))

    # Helper routine to check results
    def check(ys, data):
      # If the result was a singleton float, it should be in the original data
      if type(ys) == float:
        assert np.any([np.isclose(ys, item, equal_nan=True) for item in data])
      else:
        for bin in ys:
          # every bin is of size 1
          assert len(bin) == 1
          # every element of the bin came originally from data
          # unless it is `inf` which seems a corner case in `fcBin` not considered
          if not(np.isinf(bin[0])):
            assert np.any([np.isclose(bin[0], item, equal_nan=True) for item in data])

    check(mx, data1)
    check(my, data2)

# Test fixtures for an empty dx
test_data_dx_length_eq_zero = [
  # # Cases with empty dx
   {"x": []
  , "y": []
  , "dx": []
  , "nPerBin": 1.0
  , "mx": []
  , "my": []
  , "nBins": 0
  },

  {"x": [10.0, 8.0, 6.0, 4.0, 2.0]
  , "y": [0, 2.0, 4.0, 6.0, 8.0]
  , "dx": []
  , "nPerBin": 2.0
  , "mx": [[4.0], [8.0]]
  , "my": [[6.0], [2.0]]
  , "nBins": 2
  },

    {"x": [10.0, 8.0, 6.0, 4.0, 2.0]
  , "y": [0, 2.0, 4.0, 6.0, 8.0]
  , "dx": []
  , "nPerBin": 1.0
   , "mx": [[2.0], [4.0], [6.0], [8.0], [10.0]]
   , "my": [[8.0], [6.0], [4.0], [2.0], [0.0]]
   , "nBins": 5
  }]

# Test fixtures for scalar dx
test_data_dx_length_eq_one = [
  {"x": np.array([[5.0,10.0,20.0,10.0],[1.3,2.0,3.0,40.0]])
  , "y": np.array([[1.0,2.0,3.0,4.0],[10.0,200.0,30.0,40.0]])
  , "dx": 10.0
  , "nPerBin": 1.0
  , "mx": [[2.1],[10.0]]
  , "my": [[80.0],[3.0]]
  , "nBins": 2
   },

   {"x": np.array([[5.0,1.3],[10.0,2.0],[20.0,3.0],[10.0,40.0]])
  , "y": np.array([[1.0,10.0],[2.0,200.0],[3.0,30.0],[4.0,40.0]])
  , "dx": 10.0
  , "nPerBin": 1.0
  , "mx": [[2.1],[10.0],[20.0]]
  , "my": [[80.0],[3.0],[3.0]]
  , "nBins": 3
   },

  {"x": np.array([[5.0,1.3],[10.0,2.0],[20.0,3.0],[10.0,40.0]])
  , "y": np.array([[1.0,10.0],[2.0,200.0],[3.0,30.0],[4.0,40.0]])
  , "dx": 10.0
  , "nPerBin": 2.0
  , "mx": [[2.1], [10.0]]
  , "my": [[80.0], [3.0]]
  , "nBins": 2
   },

   {"x": np.array([[5.0,1.3],[10.0,2.0],[20.0,3.0],[10.0,40.0]])
  , "y": np.array([[1.0,10.0],[2.0,200.0],[3.0,30.0],[4.0,40.0]])
  , "dx": 10.0
  , "nPerBin": 2.1
  , "mx": [[2.1000]]
  , "my": [[80.0]]
  , "nBins": 1
   }
  ]

# Test fixtures for vector dx
test_data_dx_length_gt_one = [
   {"x": np.array([[1.0,2.0,3.0],[4.0,5.0,6.0],[7.0,8.0,9.0]])
  , "y": np.array([[10.0, 100.0, 2.0],[42.0, 29.0, 615.0], [77.0, 7.0, 12.0]])
  , "dx": [1.0, 2.0, 3.0, 4.0]
  , "nPerBin": 2
  , "mx": [[1.5],[2.5],[3.5]]
  , "my": [[55.0], [51.0], [22.0]]
  , "nBins": 3
   }
 , {"x": np.array([[1.0,2.0,3.0],[4.0,5.0,6.0],[7.0,8.0,9.0]])
  , "y": np.array([[10.0, 100.0, 2.0],[42.0, 29.0, 615.0], [77.0, 7.0, 12.0]])
  , "dx": [2.0, 3.0, 1.0]
  , "nPerBin": 2
  , "mx": [[2.5]]
  , "my": [[51.0]]
  , "nBins": 1
   }
, {"x": np.array([[1.0,2.0,3.0],[4.0,5.0,6.0],[7.0,8.0,9.0]])
  , "y": np.array([[10.0, 100.0, 2.0],[42.0, 29.0, 615.0], [77.0, 7.0, 12.0]])
  , "dx": [1.0, 10.0]
  , "nPerBin": 3
  , "mx": [[5.0]]
  , "my": [[99.3333]]
  , "nBins": 1
 }]

@pytest.mark.parametrize('data', test_data_dx_length_eq_zero +
                                 test_data_dx_length_eq_one +
                                 test_data_dx_length_gt_one)
def test_cpdBin_dx_sclar(test_engine, data):
    """
    Test cpdBin with scalar dx or empty dx
    """
    # Apply the test case
    nBins, mx, my  = test_engine.fcBin(to_matlab_type(data["x"]), to_matlab_type(data["y"]),
                                         to_matlab_type(data["dx"]), data["nPerBin"],
                                        nargout=3)
    # Check the results
    assert compare_matlab_arrays(mx, to_matlab_type(data["mx"]))
    assert compare_matlab_arrays(my, to_matlab_type(data["my"]))
    assert nBins == data["nBins"]

# Lastly test against site-specific data
def test_cpdBin_sitedata(test_engine):
    input_names  = ['x', 'y', 'dx', 'nPerBin']
    output_names = ['nBins', 'mx', 'my']
    artifacts_dir = 'tests/test_artifacts/fcBin_artifacts'
    # Get all directories within artifacts_dir
    for site_year in os.listdir(artifacts_dir):
      if os.path.isdir(f'{artifacts_dir}/{site_year}'):
        input_data = {}
        for name in input_names:
          path_to_data = f'{artifacts_dir}/{site_year}/input_{name}.csv'
          # check if the file is zero bytes or not
          if os.path.getsize(path_to_data) != 0:
            column = pd.read_csv(path_to_data, header=None).iloc[:,:].to_numpy()
            input_data[name] = matlab.double(column.tolist())
          else:
            input_data[name] = matlab.double([])

        output_data = {}
        for name in output_names:
          path_to_data = f'{artifacts_dir}/{site_year}/output_{name}.csv'
          # check if the file is zero bytes or not
          if os.path.getsize(path_to_data) != 0:
            column = pd.read_csv(path_to_data, header=None).iloc[:,:].to_numpy()
            output_data[name] = matlab.double(column.tolist())
          else:
            output_data[name] = matlab.double([])

        # Apply fcBin
        nBins, mx, my  = test_engine.fcBin(input_data["x"], input_data["y"],
                                      input_data["dx"], input_data["nPerBin"],
                                      nargout=3)

        assert compare_matlab_arrays(mx, output_data["mx"])
        assert compare_matlab_arrays(my, output_data["my"])
        assert compare_matlab_arrays(nBins, output_data["nBins"])
