# Tests for the cpdFindChangePoint20100901 function which uses linear regression to find multiple lines of best fit within a dataset
# then it identifies change points if the gradients lines of best fits are significantly different.

# Test for if n<10 

import pytest
import numpy as np
import pandas as pd
import matlab
from oneflux_steps.ustar_cp_python.cpdFindChangePoint_functions import computeReducedModels, removeOutliers, fitOperational3ParamModel


def read_csv_file(artifacts_dir, year, iteration, name, site, kind):
    """
    Generic helper to read a CSV file given an artifacts directory,
    the current year, iteration, and whether it's an input or output file.
    """
    path_to_csv = f"{artifacts_dir}/{site}_{year}_{iteration}/{kind}_{name}.csv"
    data = pd.read_csv(path_to_csv, header=None).values.tolist()
    if len(data) == 1 and len(data[0]) == 1:
        data = data[0][0]  # Unpack single values
    #if data is a single interger, return the integer, not a list
    return data


def load_data(test_engine, artifacts_dir, year, iteration, input_names, site, kind, other_dtypes=None):
    """
    Loads and converts (if necessary) input CSV data into a dictionary.
    Applies special logic for certain input data (e.g., `s3`).
    """
    if other_dtypes is None:
        other_dtypes = []
    io_data = {}
    for name in input_names:
        data = read_csv_file(artifacts_dir, year, iteration, name, site, kind)
        # Special handling for the 's3' case
        if name in other_dtypes:
            # We assume the structure is two rows that map keys to values
            io_data[name] = dict(zip(data[0], data[1]))
        elif name in ['i', 'iAbv', 'iCp3', 'iCp2']:
            io_data[name] = test_engine.convert(data, 'to_python')
        else:
            io_data[name] = test_engine.convert(data)
    return io_data

@pytest.fixture
def test_data():
    # Generate synthetic data with change points
    xx = np.linspace(0, 10, 101)
    yy = np.piecewise(xx, [xx < 3, (xx >= 3) & (xx < 7), xx >= 7],
                      [lambda x: 2 * x + 1, lambda x: -x + 10, lambda x: 0.5 * x - 0.5])
    return xx, yy


testcase_cpdFindChangePoint20100901_site_data = [('2007', x) for x in range(0, 1001, 50)]

# [ ('2007', 0), # Cp2 change point
#                                                   ('2007', 150), # No change point
#                                                   ('2007', 250), # Cp3 change point
#                                                   ('2007', 600), # Cp2 change point
#                                                   ]

@pytest.mark.parametrize('year, iteration', testcase_cpdFindChangePoint20100901_site_data)
def test_cpdFindChangePoint20100901_site_data(test_engine, year, iteration):

    # Read logged site data inputs
    input_data = {}
    input_names = ['muStar', 'mNEE']
    fPlot = 0
    cPlot = 'Test Plot'
    artifacts_dir = 'tests/test_artifacts/cpdFindChangePoint20100901_artifacts' 

    input_data = load_data(test_engine, artifacts_dir, year, iteration, input_names, 'CA-Cbo_qca_ustar', 'input')


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

    assert test_engine.equal(np.asarray(list(s2.values())), output_data['xs2']), f'Expected s2: {output_data["xs2"]}, but got: {s2.values()}'
    assert test_engine.equal(np.asarray(list(s3.values())), output_data['xs3']), f'Expected s3: {output_data["xs3"]}, but got: {s3.values()}'
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
    assert test_engine.equal(Cp2, 1.8)
    assert test_engine.equal(Cp3, 2.6)


def test_cpdFindChangePoint_invalid_input(test_engine):
    # Invalid inputs: empty arrays
    xx = test_engine.convert(np.array([]))
    yy = test_engine.convert(np.array([]))
    fPlot = 0
    cPlot = 'Invalid Input'

    # Call the MATLAB function and expect failure or NaN outputs
    Cp2, s2, Cp3, s3 = test_engine.cpdFindChangePoint20100901(
    xx, yy, fPlot, cPlot, nargout=4)

    # Assertions
    assert test_engine.equal(Cp2, float('nan')), "Cp2 should be NaN for empty input"
    assert test_engine.equal(Cp2, float('nan')), "Cp3 should be NaN for empty input"

def test_cpdFindChangePoint_insufficient_data(test_engine):
    # Insufficient data
    xx = test_engine.convert(np.array([1]))
    yy = test_engine.convert(np.array([2]))
    fPlot = 0
    cPlot = 'Insufficient Data'

    # Call the MATLAB function and expect NaN outputs
    Cp2, s2, Cp3, s3 = test_engine.cpdFindChangePoint20100901(
        xx, yy, fPlot, cPlot, nargout=4)

    # Assertions
    assert test_engine.equal(Cp2, float('nan')), "Cp2 should be NaN for insufficient data"
    assert test_engine.equal(Cp3, float('nan')), "Cp2 should be NaN for insufficient data"
    


def test_initValues(test_engine):

    cp2, cp3, s2, s3 = test_engine.initValues(nargout=4)

    s2_values = np.asarray(list(s2.values()))
    s3_values = np.asarray(list(s3.values()))


    print(cp2, cp3, s2, s3)
    assert np.isnan(s2_values).all()
    assert np.isnan(s3_values).all()
    assert test_engine.equal(cp2, float('nan'))
    assert test_engine.equal(cp3, float('nan'))

testcase_removeNans = [ (np.arange(1, 11), np.arange(1, 11), np.arange(1, 11).reshape(-1,1), np.arange(1, 11).reshape(-1,1)), # No nans
                       (np.array([1, 2, np.nan]), np.array([1, 2, 3]), np.array([[1], [2]]), np.array([[1], [2]]) ), # xx has one nan
                          (np.array([1, 2, 3]), np.array([1, np.nan, 3]), np.array([[1], [3]]), np.array([[1], [3]]) ), # yy has one nan
                            (np.array([np.nan, 2, 3]), np.array([1, 2, np.nan]), np.array([[2]]), np.array([[2]]) ), # xx and yy have nans at different indices
                            (np.array([1, 2, 3]), np.array([np.nan, np.nan, np.nan]), np.array([]), np.array([]) ), # yy has all nans
                            (np.array([np.nan, np.nan, np.nan]), np.array([1, 2, 3]), np.array([]), np.array([]) ), # xx has all nans
                            (np.array([np.nan, np.nan, np.nan]), np.array([np.nan, np.nan, np.nan]), np.array([]), np.array([]) ), # xx and yy have all nans
                            (np.array([np.nan, 2, 3]), np.array([np.nan, 2, 3]), np.array([[2], [3]]), np.array([[2], [3]]) ), # xx and yy have # nan at the same place

]
@pytest.mark.parametrize('xx, yy, expected_xx, expected_yy', testcase_removeNans)
def test_removeNans(test_engine, xx, yy, expected_xx, expected_yy):

    # Call the MATLAB function
    xx, yy = test_engine.removeNans(test_engine.convert(xx), test_engine.convert(yy), nargout=2)

    # Perform assertions
    assert test_engine.equal(xx, test_engine.convert(expected_xx))
    assert test_engine.equal(yy, test_engine.convert(expected_yy))


def outliers_array(num_outliers, size=1000, indices=None):
    x=np.ones(size)
    y=np.ones(size)

    length = len(y)
    if indices is None:
        indices = np.random.randint(0, length, size=num_outliers).tolist()
    y[indices] = 1000
    expected_x = np.delete(x, indices)
    expected_y = np.delete(y, indices)
    
    return x.reshape(-1,1), y.reshape(-1,1), expected_x.reshape(-1,1), expected_y.reshape(-1,1)

testcase_removeOutliers = \
[ (np.arange(1, 11).reshape(-1,1), np.arange(1, 11).reshape(-1,1), np.arange(1, 11).reshape(-1,1), np.arange(1, 11).reshape(-1,1)), # No outliers
    (np.arange(1, 11).reshape(-1,1), np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 500]).reshape(-1,1), np.arange(1, 11).reshape(-1,1), np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 500]).reshape(-1,1)), # *Unexpected* no outlier
    outliers_array(1), # One Outlier
    outliers_array(2), # Two Outliers
    outliers_array(3), # Three Outliers
    outliers_array(1, 10000, 1), # Outlier at beginning
    outliers_array(1, 1000, 999), # Outlier at end

]
@pytest.mark.parametrize('xx, yy, expected_x, expected_y', testcase_removeOutliers)
def test_removeOutliers(test_engine, xx, yy, expected_x, expected_y):

    n = len(xx)

    # Call the MATLAB function
    test_x, test_y = removeOutliers(xx, yy, n)
    x, y = test_engine.removeOutliers(test_engine.convert(xx), test_engine.convert(yy), n, nargout=2)

    # Perform assertions
    assert test_engine.equal(test_engine.convert(x), test_engine.convert(expected_x))
    assert test_engine.equal(test_engine.convert(y), test_engine.convert(expected_y))


## TODO: Add site data tests for computeReducedModels
testcase_computeReducedModels = [('2007', x) for x in range(0, 501, 50)]

@pytest.mark.parametrize('year, iteration', testcase_computeReducedModels)
def test_computeReducedModels(test_engine, year, iteration):

    input_data = {}
    input_names = ['x', 'y', 'n']
    artifacts_dir = 'tests/test_artifacts/computeReducedModels_artifacts' 
    input_data = load_data(test_engine, artifacts_dir, year, iteration, input_names, 'CA-Cbo_qca_ustar', 'input')


    SSERed2, SSERed3 = test_engine.computeReducedModels(*input_data.values(), nargout=2)

    output_names = ['SSERed2', 'SSERed3']
    output_data = load_data(test_engine, artifacts_dir, year, iteration, output_names, 'CA-Cbo_qca_ustar', 'output')

    assert test_engine.equal(SSERed2, output_data['SSERed2'])
    assert test_engine.equal(SSERed3, output_data['SSERed3'])

testcases_computeNEndPts = [ (100, 5), # Nominal case
                            (10, 3), # less than 0.05*n
                            (59, 3), # 1 less than 0.05*n
                            (60, 3), # Equal to 0.05*n
                            (61, 3), # 1 more than 0.05*n
                            (201, 10) # 0.05*n is not an integer
]
@pytest.mark.parametrize('n, expected_nEndPts', testcases_computeNEndPts)
def test_computeNEndPts(test_engine, n, expected_nEndPts):
    # This tests computeNEndPts function which does max(3,  floor(0.05 * n))

    nEndPts = test_engine.computeNEndPts(n)

    test_engine.equal(nEndPts, expected_nEndPts)

testcase_updateS2 = [('2007', x) for x in range(0, 901, 50)]
@pytest.mark.parametrize('year, iteration', testcase_updateS2)
def test_updateS2(test_engine, year, iteration):
    # Define test inputs
    input_data = {}
    input_names = ['a2', 'a2int', 'Cp2', 'Fmax2', 'p2', 's2']
    artifacts_dir = 'tests/test_artifacts/updateS2_artifacts' 

    input_data = load_data(test_engine, artifacts_dir, year, iteration, input_names, 'CA-Cbo_qca_ustar', 'input', ['s2'])
    
    s2 = test_engine.updateS2(*input_data.values(), nargout=1)

    path_to_artifacts = artifacts_dir + f'/CA-Cbo_qca_ustar_{year}_{iteration}/output_s2.csv'
    expected_s2 = pd.read_csv(path_to_artifacts, header=None)
    expected_s2 = np.asarray(expected_s2.values.tolist()[1], dtype=float)

    s2_values = np.asarray(list(s2.values()), dtype=float)

    assert test_engine.equal(test_engine.convert(s2_values), test_engine.convert(expected_s2))




testcase_updateS3 = [('2007', x) for x in range(0, 901, 50)]
@pytest.mark.parametrize('year, iteration', testcase_updateS3)
def test_updateS3(test_engine, year, iteration):
    # Define test inputs
    input_data = {}
    input_names = ['a3', 'a3int', 'xCp3', 'Fmax3', 'p3', 's3']
    artifacts_dir = 'tests/test_artifacts/updateS3_artifacts' 

    input_data = load_data(test_engine, artifacts_dir, year, iteration, input_names, 'CA-Cbo_qca_ustar', 'input', ['s3'])

    
    s3 = test_engine.updateS3(*input_data.values(), nargout=1)

    path_to_artifacts = artifacts_dir + f'/CA-Cbo_qca_ustar_{year}_{iteration}/output_s3.csv'
    expected_s3 = pd.read_csv(path_to_artifacts, header=None)
    expected_s3 = np.asarray(expected_s3.values.tolist()[1], dtype=float)

    s3_values = np.asarray(list(s3.values()), dtype=float)

    assert test_engine.equal(test_engine.convert(s3_values), test_engine.convert(expected_s3))


testcase_fitOperational2ParamModel = [('2007', x) for x in range(0, 1001, 50)]

@pytest.mark.parametrize('year, iteration', testcase_fitOperational2ParamModel)
def test_fitOperational2ParamModel(test_engine, year, iteration):

    input_names = ['i', 'n', 'x', 'y', 'SSERed2', 'Fc2']
    artifacts_dir = 'tests/test_artifacts/fitOperational2ParamModel_artifacts' 

    input_data = load_data(test_engine, artifacts_dir, year, iteration, input_names, 'CA-Cbo_qca_ustar', 'input')
    iAbv, Fc2 = test_engine.fitOperational2ParamModel(*input_data.values(), nargout=2)

    output_names = ['iAbv', 'Fc2']
    output_data = load_data(test_engine, artifacts_dir, year, iteration, output_names, 'CA-Cbo_qca_ustar', 'output')


    assert test_engine.equal(iAbv, output_data['iAbv'])
    assert test_engine.equal(Fc2, output_data['Fc2'])


testcase_fitOperational3ParamModel = [('2007', x) for x in range(0, 1001, 50)]

@pytest.mark.parametrize('year, iteration', testcase_fitOperational3ParamModel)
def test_fitOperational3ParamModel(test_engine, year, iteration):

    input_names = ['i', 'iAbv', 'n', 'x', 'y', 'SSERed3', 'Fc3']
    artifacts_dir = 'tests/test_artifacts/fitOperational3ParamModel_artifacts' 
 
    input_data = load_data(test_engine, artifacts_dir, year, iteration, input_names, 'CA-Cbo_qca_ustar', 'input')

    Fc3 = test_engine.fitOperational3ParamModel(*input_data.values(), nargout=1)

    output_names = ['Fc3']
    output_data = load_data(test_engine, artifacts_dir, year, iteration, output_names, 'CA-Cbo_qca_ustar', 'output')


    assert test_engine.equal(Fc3, output_data['Fc3'])


testcase_fitThreeParameterModel = [('2007', x) for x in range(0, 1001, 50)]

@pytest.mark.parametrize('year, iteration', testcase_fitThreeParameterModel)
def test_fitThreeParameterModel(test_engine, year, iteration):

    input_names = ['Fc3', 'x', 'y', 'n', 'pSig']
    artifacts_dir = 'tests/test_artifacts/fitThreeParameterModel_artifacts'

    input_data = load_data(test_engine, artifacts_dir, year, iteration, input_names, 'CA-Cbo_qca_ustar', 'input')

    Fmax3, iCp3, xCp3, a3, a3int, yHat3, p3, Cp3 = test_engine.fitThreeParameterModel(*input_data.values(), nargout=8)

    output_names = ['Fmax3', 'iCp3', 'xCp3', 'a3', 'a3int', 'yHat3', 'p3', 'Cp3']

    output_data = load_data(test_engine, artifacts_dir, year, iteration, output_names, 'CA-Cbo_qca_ustar', 'output')

    assert test_engine.equal(Fmax3, output_data['Fmax3'])
    assert test_engine.equal(iCp3, output_data['iCp3'])
    assert test_engine.equal(xCp3, output_data['xCp3'])
    assert test_engine.equal(a3, output_data['a3'])
    assert test_engine.equal(a3int, output_data['a3int'])
    assert test_engine.equal(yHat3, output_data['yHat3'])
    assert test_engine.equal(p3, output_data['p3'])
    assert test_engine.equal(Cp3, output_data['Cp3'])


testcase_fitTwoParameterModel = [('2007', x) for x in range(0, 1001, 50)]

@pytest.mark.parametrize('year, iteration', testcase_fitTwoParameterModel)
def test_fitTwoParameterModel(test_engine, year, iteration):

    input_names = ['Fc2', 'x', 'y', 'n', 'pSig']
    artifacts_dir = 'tests/test_artifacts/fitTwoParameterModel_artifacts'

    input_data = load_data(test_engine, artifacts_dir, year, iteration, input_names, 'CA-Cbo_qca_ustar', 'input')

    Fmax2, iCp2, xCp2, a2, a2int, yHat2, p2, Cp2 = test_engine.fitTwoParameterModel(*input_data.values(), nargout=8)

    output_names = ['Fmax2', 'iCp2', 'xCp2', 'a2', 'a2int', 'yHat2', 'p2', 'Cp2']

    output_data = load_data(test_engine, artifacts_dir, year, iteration, output_names, 'CA-Cbo_qca_ustar', 'output')

    assert test_engine.equal(Fmax2, output_data['Fmax2'])
    assert test_engine.equal(iCp2, output_data['iCp2'])
    assert test_engine.equal(xCp2, output_data['xCp2'])
    assert test_engine.equal(a2, output_data['a2'])
    assert test_engine.equal(a2int, output_data['a2int'])
    assert test_engine.equal(yHat2, output_data['yHat2'])
    assert test_engine.equal(p2, output_data['p2'])
    assert test_engine.equal(Cp2, output_data['Cp2'])

    