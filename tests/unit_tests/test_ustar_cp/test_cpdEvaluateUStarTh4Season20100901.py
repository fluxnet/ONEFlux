"""
Test module for the cpdEvaluateUStarTh4Season20100901 matlab function.

This module contains the unit tests for the cpdEvaluateUStarTh4Season20100901. 
These tests cover basic behaviour, edge cases and errors.
"""

import pytest
import matlab.engine
import numpy as np
import pandas as pd
import json
import os
from typing import Tuple
from oneflux_steps.ustar_cp_python.cpd_evaluate_functions import *


rng = np.random.default_rng()

def json_to_numpy(data):
    
    all_arrays = []
    for record_group in data:  # Handle nested lists in the JSON
        group_arrays = []
        for record in record_group:
            array = np.array(list(record.values()), dtype=float)  # Convert to numpy array
            group_arrays.append(array)
        all_arrays.append(np.array(group_arrays))  # Group into a 2D array for each group
    return np.array(all_arrays)

# def test_test_engine(test_engine):
#     """
#     Test the test engine.
#     """
#     x = test_engine.prctile([1,2,3,4,5], 50)
#     print(x)

#     assert 1==0

cpdEvaluateUStar_test_cases = ['2007', # Nomial case 
                               '2007_fnight_zero_0' # All nighttime data is zero
                               ]
@pytest.mark.parametrize('year', cpdEvaluateUStar_test_cases)
def test_cpdEvaluateUStarTh4Season20100901_logged_data(test_engine, year): # This test stores the logged data as row major instead of column major
    """
    Test the cpdEvaluateUStarTh4Season20100901 function.
    """
    if test_engine.cpdEvaluateUStarTh4Season20100901 is None:
        pytest.skip("Test function not available")
    input_data = {}
    input_names = ['t_it_', 'NEE_it_', 'updated_uStar_it_', 'T_it_', 'fNight_it_']
    fplot = 0
    cSiteYr = f'CA-Cbo_qca_ustar_{year}.csv' 
    artifacts_dir = 'tests/test_artifacts/cpdEvaluateUStarTh4Season20100901_artifacts' 
    for name in input_names:
        path_to_artifacts = artifacts_dir + f'/CA-Cbo_qca_ustar_{year}/input_{name}.csv'
        column = pd.read_csv(path_to_artifacts, header=None).iloc[:,0].to_numpy()
        input_data[name] = test_engine.convert(column)

    [xCp2,xStats2, xCp3,xStats3] = test_engine.cpdEvaluateUStarTh4Season20100901(
        input_data['t_it_'], input_data['NEE_it_'], input_data['updated_uStar_it_'], 
        input_data['T_it_'], input_data['fNight_it_'], fplot, cSiteYr, 1, nargout=4)
    
    expected_xCp2 = artifacts_dir + f"/CA-Cbo_qca_ustar_{year}/output_xCp2.csv"
    expected_xCp2 = pd.read_csv(expected_xCp2, header=None).iloc[:,:].to_numpy()

    expected_xCp3 = artifacts_dir + f"/CA-Cbo_qca_ustar_{year}/output_xCp3.csv"
    expected_xCp3 = pd.read_csv(expected_xCp3, header=None).iloc[:,:].to_numpy()

    expected_xStats2 = artifacts_dir + f"/CA-Cbo_qca_ustar_{year}/output_xStats2.json"
    expected_xStats3 = artifacts_dir + f"/CA-Cbo_qca_ustar_{year}/output_xStats3.json"
    
    xStats2 = json_to_numpy(json.loads(xStats2))
    xStats3 = json_to_numpy(json.loads(xStats3))

    with open(expected_xStats2, 'r') as f:
        expected_xStats2 = json_to_numpy(json.load(f))
    with open(expected_xStats3, 'r') as f:
        expected_xStats3 = json_to_numpy(json.load(f))

    assert test_engine.equal(test_engine.convert(xStats2), expected_xStats2)
    assert test_engine.equal(test_engine.convert(xStats3), expected_xStats3)
    assert test_engine.equal(test_engine.convert(xCp2), expected_xCp2)
    assert test_engine.equal(test_engine.convert(xCp3), expected_xCp3)


testcases = [ ([1.0000, 1.0417, 1.0834], 3, [0,1,1], 366, 3, 2400), #nPerDay = 24, nPerBin = 3
                ([1.083, 1.083, 1.125], 3, [1,1,1], 366, 5, 4000) # nPerBin = 5
                ]
@pytest.mark.parametrize('t, expected_nt, expected_m, expected_EndDOY, expected_nPerBin, expected_nN', testcases)
def test_initializeParameters(test_engine, t, expected_nt, expected_m, expected_EndDOY, expected_nPerBin, expected_nN):
    """
    Tests the initializeParameters function.
    """
    if test_engine.initializeParameters is None:
        pytest.skip("Test function not available")
    nSeasons = 4
    nStrataN = 4
    nBins = 50
    t = test_engine.convert(t)

    nt, m, EndDOY, nPerBin, nN = test_engine.initializeParameters(t, nSeasons, nStrataN, nBins, nargout=5)
    
    assert test_engine.equal(nt, expected_nt)
    assert test_engine.equal(m, expected_m)
    assert test_engine.equal(EndDOY, expected_EndDOY)
    assert test_engine.equal(nPerBin, expected_nPerBin)
    assert test_engine.equal(nN, expected_nN)


uStar_some_nans = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, np.nan])
NEE_some_nans = np.array([1, 2, 3, np.nan, 5, 6, 7, 8, 9, 10])
T_some_nans = np.array([1, 2, 3, 4, 5, 6, 7, np.nan, 9, 10])
testcases = [ 
            (uStar_some_nans, np.random.randint(0, 2, size=10), rng.uniform(-20,20,10), rng.uniform(-20,20,10)), #uStar some nans
            (rng.uniform(-20,20,10), np.random.randint(0, 2, size=10), NEE_some_nans, rng.uniform(-20,20,10)), #NEE some nans
            (rng.uniform(-20,20,10), np.random.randint(0, 2, size=10), rng.uniform(-20,20,10), T_some_nans), #T some nans
            (rng.uniform(-20,20,10), np.random.randint(0, 2, size=10), rng.uniform(-20,20,10), rng.uniform(-20,20,10)), # No nans
            (rng.uniform(-20,20,10), np.ones(10), rng.uniform(-20,20,10), rng.uniform(-20,20,10)), #fNight all zeros
            (rng.uniform(-20,20,10), np.zeros(10), rng.uniform(-20,20,10), rng.uniform(-20,20,10)), #fNight all zeros
            ]

@pytest.mark.parametrize('uStar, fNight, NEE, T', testcases)
def test_filterInvalidPoints(test_engine, uStar, fNight, NEE, T):
    """
    Test the filterInvalidPoints function.
    """
    
    expected_u_star, expected_valid_annual_indices, expected_num_valid_annual = filterInvalidPoints(uStar, fNight, NEE, T)
    expected_u_star, expected_valid_annual_indices, expected_num_valid_annual = \
        test_engine.convert(expected_u_star), test_engine.convert(expected_valid_annual_indices, 'to_matlab'), test_engine.convert(expected_num_valid_annual) # +1 to account for 1-based indexing in MATLAB
    
    uStar = test_engine.convert(uStar)
    fNight = test_engine.convert(fNight)
    NEE = test_engine.convert(NEE)
    T = test_engine.convert(T)

    uStar, itAnnual, ntAnnual = test_engine.filterInvalidPoints(uStar, fNight, NEE, T, nargout=3)

    assert test_engine.equal(test_engine.convert(uStar), expected_u_star)
    assert test_engine.equal(test_engine.convert(itAnnual), expected_valid_annual_indices)
    assert test_engine.equal(test_engine.convert(ntAnnual), expected_num_valid_annual)


def test_filterInvalidPoints_logged_data(test_engine):
    """
    Test the filterInvalidPoints function.
    """
    artifacts_dir = 'tests/test_artifacts/filterInvalidPoints_artifacts'
    input_names = ['fNight', 'NEE', 'uStar', 'T']
    input_data = {}
    for name in input_names:
        path_to_artifacts = artifacts_dir + f'/CA-Cbo_qca_ustar_2007_0/input_{name}.csv'
        column = pd.read_csv(path_to_artifacts, header=None).iloc[:,0].to_numpy()
        input_data[name] = test_engine.convert(column)
    
    expected_output_names = ['uStar', 'itAnnual', 'ntAnnual']
    expected_output_data = {}
    for name in expected_output_names:
        path_to_artifacts = artifacts_dir + f'/CA-Cbo_qca_ustar_2007_0/output_{name}.csv'
        column = pd.read_csv(path_to_artifacts, header=None).iloc[:,0].to_numpy()
        if name == 'itAnnual':
            expected_output_data[name] = test_engine.convert(column, 'to_python')
        else:
            expected_output_data[name] = test_engine.convert(column)

    uStar, itAnnual, ntAnnual = test_engine.filterInvalidPoints(input_data['uStar'], input_data['fNight'], input_data['NEE'], input_data['T'], nargout=3)
    print("output: ", itAnnual)
    print("expected: ", expected_output_data['itAnnual'])
    assert test_engine.equal(test_engine.convert(uStar), expected_output_data['uStar'])
    assert test_engine.equal(test_engine.convert(itAnnual), expected_output_data['itAnnual'])
    assert test_engine.equal(test_engine.convert(ntAnnual), expected_output_data['ntAnnual'])



def test_initializeStatistics(test_engine):
    """
    Test the initializeStatistics function initiliazes the Stats2 and Stats3 structures with NaN values.
    """
    if test_engine.initializeStatistics is None:
        pytest.skip("Test function not available")
    nSeasons = 4
    nStrataX = 8

    Stats2, Stats3 = test_engine.initializeStatistics(nSeasons, nStrataX, 1, nargout=2)
    Stats2 = json.loads(Stats2)
    Stats3 = json.loads(Stats3)
    assert len(Stats2) == 4, "Stats2 should have 4 entries for each season."
    assert len(Stats3) == 4, "Stats3 should have 4 entries for each season."
    # print(Stats2)
    # print(Stats3)

    # Check the structure of Stats2 and Stats3
    struct = set(['n', 'Cp', 'Fmax', 'p', 'b0', 'b1', 'b2', 'c2', 'cib0', 'cib1', 'cic2', 'mt' , 'ti', 'tf', 'ruStarVsT', 'puStarVsT', 'mT', 'ciT'])
    for s2, s3 in zip(Stats2, Stats3):
        for i in range(nStrataX): 
                assert set(s2[i].keys()) == struct
                assert set(s3[i].keys()) == struct

                temp_s2 = np.array(list(s2[i].values()), dtype=float) # Convert to numpy array
                temp_s3 = np.array(list(s3[i].values()), dtype=float)
                assert np.isnan(temp_s2).any() == True # Checks all values are NaN
                assert np.isnan(temp_s3).any() == True


occurrences = 50
size = 600
testcases = [
               (rng.uniform(0,5,size), rng.uniform(0,5,size), rng.uniform(0,5,size), rng.uniform(0,5,size), np.random.randint(0,2,size), 366, np.repeat(np.arange(1, 13), occurrences), size), # Nominal case
                (rng.uniform(0,5,size), rng.uniform(0,5,size), rng.uniform(0,5,size), rng.uniform(0,5,size), np.ones(size), 366, np.repeat(np.arange(1, 13), occurrences), size), # All nighttime data
                (rng.uniform(0,5,size), rng.uniform(0,5,size), rng.uniform(0,5,size), rng.uniform(0,5,size), np.zeros(size), 366, np.repeat(np.arange(1, 13), occurrences), size) # All daytime data
             ]
@pytest.mark.parametrize('t, T, uStar, NEE, fNight, EndDOY, m, nt', testcases)
def test_reorderAndPreprocessData(test_engine, t, T, uStar, NEE, fNight, EndDOY, m, nt):
    """
    Test the reorderAndPreprocessData function.
    """
    data = [t, T, uStar, NEE, fNight, EndDOY, m, nt]
    
    matlab_data = [test_engine.convert(d) for d in data]
    t, T, uStar, NEE, fNight, itAnnual, ntAnnual = test_engine.reorderAndPreprocessData(*matlab_data, nargout=7)
    # t = test_engine.reorderAndPreprocessData(*matlab_data, nargout=1)
    expected_t, expected_T, expected_uStar, expected_NEE, expected_fNight, expected_itAnnual, expected_ntAnnual = reorderAndPreprocessData(*data)
    # result = reorder_and_preprocess_data(*data)
    # print(t[:10])
    # print(expected_t[:10])
    # print(result)
    assert test_engine.equal(test_engine.convert(t), expected_t)
    assert test_engine.equal(test_engine.convert(T), expected_T)
    assert test_engine.equal(test_engine.convert(uStar), expected_uStar)
    assert test_engine.equal(test_engine.convert(NEE), expected_NEE)
    assert test_engine.equal(test_engine.convert(fNight), expected_fNight)
    assert test_engine.equal(test_engine.convert(itAnnual), test_engine.convert(expected_itAnnual, 'to_matlab')) # +1 to match matlab indexings
    assert test_engine.equal(ntAnnual, expected_ntAnnual)


def test_reorderAndPreprocessData_logged_data(test_engine):
    """
    Test the reorderAndPreprocessData function.
    """
    artifacts_dir = 'tests/test_artifacts/reorderAndPreprocessData_artifacts'
    input_names = ['t', 'T', 'uStar', 'NEE', 'fNight', 'EndDOY', 'm', 'nt']
    input_data = {}
    for name in input_names:
        path_to_artifacts = artifacts_dir + f'/CA-Cbo_qca_ustar_2007_0/input_{name}.csv'
        column = pd.read_csv(path_to_artifacts, header=None).iloc[:,0].to_numpy()
        if name in {'EndDOY', 'nt'}:
            input_data[name] = test_engine.convert(int(column[0]))
        else:
            input_data[name] = test_engine.convert(column)

    expected_output_names = ['t', 'T', 'uStar', 'NEE', 'fNight', 'itAnnual', 'ntAnnual']
    expected_output_data = {}
    for name in expected_output_names:
        path_to_artifacts = artifacts_dir + f'/CA-Cbo_qca_ustar_2007_0/output_{name}.csv'
        column = pd.read_csv(path_to_artifacts, header=None).iloc[:,0].to_numpy()
        if name == 'itAnnual':
            expected_output_data[name] = test_engine.convert(column, 'to_python')
        else:
            expected_output_data[name] = test_engine.convert(column)
        
    t, T, uStar, NEE, fNight, itAnnual, ntAnnual = test_engine.reorderAndPreprocessData(*[input_data[name] for name in input_names], nargout=7)

    assert test_engine.equal(test_engine.convert(t), expected_output_data['t'])
    assert test_engine.equal(test_engine.convert(T), expected_output_data['T'])
    assert test_engine.equal(test_engine.convert(uStar), expected_output_data['uStar'])
    assert test_engine.equal(test_engine.convert(NEE), expected_output_data['NEE'])
    assert test_engine.equal(test_engine.convert(fNight), expected_output_data['fNight'])
    assert test_engine.equal(test_engine.convert(itAnnual), expected_output_data['itAnnual'])
    assert test_engine.equal(ntAnnual, test_engine.convert(expected_output_data['ntAnnual']))


testcases = [
    (1, 4, 1000/4, 1000, range(1, 251)), # iSeasons = 1
    (2, 4, 1000/4, 1000, range(251, 500+1)), # iSeasons = 2
    (3, 4, 1000/4, 1000, range(501, 750+1)), # iSeasons = 3
    (4, 4, 1000/4, 1000, range(751, 1000+1)), # iSeasons = 4
    (1, 4, round(2055/4), 2055, range(1, 514+1)), # iSeasons = 1, ntAnnual is odd
    (2, 4, round(3879/4), 3879, range(971, 1940+1)), # iSeasons = 2, ntAnnual is odd
    (3, 4, round(5347/4), 5347, range(2675, 4011+1)), # iSeasons = 3, ntAnnual is odd
    (4, 4, round(4999/4), 4999, range(3751, 4999+1)), # iSeasons = 4, ntAnnual is odd
]
@pytest.mark.parametrize('iSeasons, nSeasons, nPerSeason, ntAnnual, expected_jtSeasons', testcases)
def test_computeSeasonIndices(test_engine, iSeasons, nSeasons, nPerSeason, ntAnnual, expected_jtSeasons):
    """
    Test the computeSeasonIndices function.
    """

    python_jtSeasons = computeSeasonIndices(iSeasons, nSeasons, nPerSeason, ntAnnual)

    jtSeasons = test_engine.computeSeasonIndices(iSeasons, nSeasons, nPerSeason, test_engine.convert(ntAnnual))


    assert test_engine.equal(test_engine.convert(jtSeasons), test_engine.convert(expected_jtSeasons))
    assert test_engine.equal(test_engine.convert(python_jtSeasons), expected_jtSeasons)
    

testcases = [
             (1339, 5, 5), # Nominal case, nStrata between 4 and 8
             (1339, 3, 8), # nStrata > 8, ntSeason is not perfectly divisible
             (1500, 3, 8), # nStrata > 8, ntSeason is perfectly divisible
             (2000, 5, 8), # nStrata = 8, ntSeason is perfectly divisible
             (1000, 5, 4), # nStrata = 4, ntSeason is perfectly divisible
             (369, 3, 4), # nStrata < 4, ntSeason is not perfectly divisible
             (750, 5, 4) # nStrata < 4, ntSeason is perfectly divisible
             ]

@pytest.mark.parametrize('ntSeason, nPerBin, expected_nStrata', testcases)
def test_computeStrataCount(test_engine, ntSeason, nPerBin, expected_nStrata):
    """
    Test the computeStrataCount function.
    """
    nStrataX = 8
    nStrataN = 4
    nBins = 50

    python_nStrata = computeStrataCount(ntSeason, nBins, nPerBin, nStrataN, nStrataX)
    nStrata = test_engine.computeStrataCount(ntSeason, nBins, nPerBin, nStrataN, nStrataX)

    assert test_engine.equal(test_engine.convert(nStrata), expected_nStrata)
    assert test_engine.equal(test_engine.convert(python_nStrata), expected_nStrata)


def test_computeTemperatureThresholds_logged_data(test_engine):
    """
    Test the computeTemperatureTresholds function.
    Tests a single case, matlab function is essentially a wrapper to the matlab percentile function but with a contrained statespace of inputs.
    """
    nStrata = 5
    artifacts_dir = 'tests/test_artifacts/computeTemperatureThresholds_artifacts'
    input_names = ['T', 'itSeason']
    input_data = {}
    for name in input_names:
        path_to_artifacts = artifacts_dir + f'/CA-Cbo_qca_ustar_2007_0/input_{name}.csv'
        column = pd.read_csv(path_to_artifacts, header=None).iloc[:,0].to_numpy()
        input_data[name] = column#.tolist()
    print(input_data['itSeason'])
    print(test_engine.convert(input_data['itSeason'], 'to_python'))
    TTh = test_engine.computeTemperatureThresholds(test_engine.convert(input_data['T']), test_engine.convert(input_data['itSeason'], 'to_python'), nStrata, nargout=1)
    python_TTh = computeTemperatureThresholds(np.array(input_data['T']), input_data['itSeason']-1, nStrata) # -1 to account for 0-based indexing in python

    expected_TTh = artifacts_dir + f'/CA-Cbo_qca_ustar_2007_0/output_TTh.csv'
    expected_TTh = pd.read_csv(expected_TTh, header=None).iloc[0,:].to_numpy()
    print("test_engine output: ", TTh)
    print("expected output: ", expected_TTh)
    assert test_engine.equal(test_engine.convert(TTh), test_engine.convert(expected_TTh))
    assert test_engine.equal(test_engine.convert(python_TTh), test_engine.convert(expected_TTh))

tetcases = [
    (rng.uniform(-20,20,1000), np.array(rng.choice(1000, size=500, replace=False)), [-14.601,-5.22904,-2.095605,1.836835,5.136015,14.2835], 0), # Nominal case
    (np.array([-20, -19, -15, 1, 4 ,14, 8, 7, 8 ,4], dtype=float), np.array([0, 1, 2]), [-14.601,-5.22904,-2.095605,1.836835,5.136015,14.2835], 1), # # No matching indices
    (np.array([-1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], dtype=float), np.array([4, 7, 9]), [1, 1, 1, 1, 1, 1], 4), # Non increasing threshold TTH 
    (rng.uniform(-5,25,900), np.array(rng.choice(1000, size=300, replace=False)), [-1.34166,5.217795,8.340625,12.45965,16.9017,24.672], 2), # iStrata = 2
    (rng.uniform(0,30,400), np.array(rng.choice(1000, size=200, replace=False)), [2.34335,6.89097,11.09125,14.6745,17.95015,27.262], 4), # iStrata = 4
    (rng.uniform(-5,15,800), np.array(rng.choice(1000, size=400, replace=False)), [-2.22904,0.904395,4.836835,8.136015,13.2835], 3), # iStrata = 3, length(TTh) = 5

]
@pytest.mark.parametrize('T, itSeason, TTh, iStrata', tetcases)
def test_findStratumIndices(test_engine, T, itSeason, TTh, iStrata):
    """
    Test the findStratumIndices function.
    """
    expected_itStrata = findStratumIndices(T, itSeason, TTh, iStrata)

    T = test_engine.convert(T)
    itSeason = test_engine.convert(np.array(itSeason, dtype=float), 'to_matlab') # +1 to account for 1-based indexing in MATLAB
    TTh = test_engine.convert(TTh)
    iStrata = test_engine.convert(iStrata, 'to_matlab') # +1 to account for 1-based indexing in MATLAB

    itStrata = test_engine.findStratumIndices(T, itSeason, TTh, iStrata, nargout=1)

    assert test_engine.equal(itStrata, test_engine.convert(expected_itStrata, 'to_matlab')) # +1 to account for 1-based indexing in matlab


def test_addStatisticsFields(test_engine):
    """
    Test the addStatistics function.
    """
    #print(test_engine.addStatisticsFields)
    # Generate input data
    rng = np.random.default_rng()
    xs_keys = ['n', 'Cp', 'Fmax', 'p', 'b0', 'b1', 'b2', 'c2', 'cib0', 'cib1', 'cic2', 'mt' , 'ti', 'tf', 'ruStarVsT', 'puStarVsT', 'mT', 'ciT']
    xs = {key:np.nan for key in xs_keys}
    t = np.linspace(0, 10, 500)
    r = [[1, 0.429039265010557],[0.429039265010557, 1]]
    p = [[1, 0.00120739842384987], [0.00120739842384987, 1]]
    T = rng.uniform(-20,20,1000)
    itStrata = np.array(list(range(1,51)) + list(range(200,300)))

    xs = test_engine.addStatisticsFields(xs, test_engine.convert(t), test_engine.convert(r), \
                                          test_engine.convert(p), test_engine.convert(T), test_engine.convert(itStrata, 'to_matlab'), nargout=1)
    print("test_engine output: ",xs)
    expected_xs = {}
    expected_xs = addStatisticsFields(expected_xs, t, r, p, T, itStrata)

    output_xs = np.array([xs['mt'], xs['ti'], xs['tf'], xs['ruStarVsT'], xs['puStarVsT'], xs['mT'], xs['ciT']])
    print(output_xs)
    print(expected_xs)    
    assert test_engine.equal(test_engine.convert(list(expected_xs.values())), output_xs)

