# Tests for the cpdFindChangePoint20100901 function which uses linear regression to find multiple lines of best fit within a dataset
# then it identifies change points if the gradients lines of best fits are significantly different.

# Test for if n<10 

import pytest
import numpy as np
import pandas as pd
import matlab

@pytest.fixture
def test_data():
    # Generate synthetic data with change points
    xx = np.linspace(0, 10, 101)
    yy = np.piecewise(xx, [xx < 3, (xx >= 3) & (xx < 7), xx >= 7],
                      [lambda x: 2 * x + 1, lambda x: -x + 10, lambda x: 0.5 * x - 0.5])
    return xx, yy


testcase_cpdFindChangePoint20100901_site_data = [ ('2007', 0), # Cp2 change point
                                                  ('2007', 150), # No change point
                                                  ('2007', 250), # Cp3 change point
                                                  ('2007', 600), # Cp2 change point
                                                  ]
@pytest.mark.parametrize('year, iteration', testcase_cpdFindChangePoint20100901_site_data)
def test_cpdFindChangePoint20100901_site_data(test_engine, year, iteration):

    # Read logged site data inputs
    input_data = {}
    input_names = ['muStar', 'mNEE']
    fPlot = 0
    cPlot = 'Test Plot'
    cSiteYr = f'CA-Cbo_qca_ustar_{year}.csv' 
    artifacts_dir = 'tests/test_artifacts/cpdFindChangePoint20100901_artifacts' 
    for name in input_names:
        path_to_artifacts = artifacts_dir + f'/CA-Cbo_qca_ustar_{year}_{iteration}/input_{name}.csv'
        column = pd.read_csv(path_to_artifacts, header=None).iloc[:,0].to_numpy()
        input_data[name] = test_engine.convert(column)

    Cp2, s2, Cp3, s3 = test_engine.cpdFindChangePoint20100901(input_data['muStar'], input_data['mNEE'], fPlot, cPlot, nargout=4)

    # Read logged site data expected output data
    output_names = ['xCp2', 'xs2', 'xCp3', 'xs3']
    output_data = {}
    for name in output_names:
        path_to_artifacts = artifacts_dir + f'/CA-Cbo_qca_ustar_{year}_{iteration}/output_{name}.csv'
        if name in ['xs2', 'xs3']:
            output_data[name] = pd.read_csv(path_to_artifacts, header=None).iloc[1,:].to_numpy(dtype=float)
        else:
            output_data[name] = pd.read_csv(path_to_artifacts, header=None).iloc[:,0].to_numpy()
             

    assert test_engine.equal((list(s2.values())), output_data['xs2'], ), f'Expected s2: {output_data["xs2"]}, but got: {s2.values()}'
    assert test_engine.equal((list(s3.values())), output_data['xs3']), f'Expected s3: {output_data["xs3"]}, but got: {s3.values()}'
    assert test_engine.equal(Cp2, output_data['xCp2']), f'Expected Cp2: {output_data["Cp2"]}, but got: {Cp2}'
    assert test_engine.equal(Cp3, output_data['xCp3']), f'Expected Cp3: {output_data["Cp3"]}, but got: {Cp3}'


def test_cpdFindChangePoint20100901(test_engine, test_data):
    # Define test inputs
    xx, yy = test_data
    fPlot = 0
    cPlot = 'Test Plot'

    # Call the MATLAB function
    Cp2, s2, Cp3, s3 = test_engine.cpdFindChangePoint20100901(xx, yy, fPlot, cPlot, nargout=4)

    s2_values = np.asarray(list(s2.values()))
    s3_values = np.asarray(list(s3.values()))
    
    # Perform assertions
    assert isinstance(Cp2, float)
    assert isinstance(Cp3, float)
    assert isinstance(s2, dict)
    assert isinstance(s3, dict)
    assert np.issubdtype(s2_values.dtype, float)
    assert np.issubdtype(s3_values.dtype, float)

    # Additional checks based on expected output
    assert s2['n'] == len(xx)
    assert s3['n'] == len(xx)
    assert Cp2 == 1.8
    assert Cp3 == 2.6


def test_cpdFindChangePoint_invalid_input(test_engine):
    # Invalid inputs: empty arrays
    xx = np.array([])
    yy = np.array([])
    fPlot = 0
    cPlot = 'Invalid Input'

    # Call the MATLAB function and expect failure or NaN outputs
    Cp2, s2, Cp3, s3 = test_engine.cpdFindChangePoint20100901(
        matlab.double(xx.tolist()), matlab.double(yy.tolist()), fPlot, cPlot, nargout=4)

    # Assertions
    assert np.isnan(Cp2), "Cp2 should be NaN for empty input"
    assert np.isnan(Cp3), "Cp3 should be NaN for empty input"

def test_cpdFindChangePoint_insufficient_data(test_engine):
    # Insufficient data
    xx = np.array([1])
    yy = np.array([2])
    fPlot = 0
    cPlot = 'Insufficient Data'

    # Call the MATLAB function and expect NaN outputs
    Cp2, s2, Cp3, s3 = test_engine.cpdFindChangePoint20100901(
        matlab.double(xx.tolist()), matlab.double(yy.tolist()), fPlot, cPlot, nargout=4)

    # Assertions
    assert np.isnan(Cp2), "Cp2 should be NaN for insufficient data"
    assert np.isnan(Cp3), "Cp3 should be NaN for insufficient data"