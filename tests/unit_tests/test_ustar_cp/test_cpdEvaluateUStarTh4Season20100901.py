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
from oneflux_steps.ustar_cp_python.cpd_evaluate_functions import reorder_and_preprocess_data, filter_invalid_points, addStatisticsFields


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




cpdEvaluateUStar_test_cases = ['2007', # Nomial case 
                               '2007_fnight_zero_0' # All nighttime data is zero
                               ]
@pytest.mark.parametrize('year', cpdEvaluateUStar_test_cases)
def test_cpdEvaluateUStarTh4Season20100901_logged_data(matlab_engine, year): # This test stores the logged data as row major instead of column major
    """
    Test the cpdEvaluateUStarTh4Season20100901 function in MATLAB.
    """

    input_data = {}
    input_names = ['t_it_', 'NEE_it_', 'updated_uStar_it_', 'T_it_', 'fNight_it_']
    fplot = 0
    cSiteYr = f'CA-Cbo_qca_ustar_{year}.csv' 
    artifacts_dir = 'tests/test_artifacts/cpdEvaluateUStarTh4Season20100901_artifacts' 
    for name in input_names:
        path_to_artifacts = artifacts_dir + f'/CA-Cbo_qca_ustar_{year}/input_{name}.csv'
        column = pd.read_csv(path_to_artifacts, header=None).iloc[:,0].to_numpy()
        input_data[name] = matlab.double(column.tolist())

    [xCp2,xStats2, xCp3,xStats3] = matlab_engine.cpdEvaluateUStarTh4Season20100901(
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

    xCp2 = xCp2.tomemoryview().tolist()
    xCp2 = np.array(xCp2)

    assert np.allclose(xStats2, expected_xStats2, equal_nan=True)
    assert np.allclose(xStats3, expected_xStats3, equal_nan=True)
    assert np.allclose(xCp2, expected_xCp2, equal_nan=True)
    assert np.allclose(xCp3, expected_xCp3, equal_nan=True)


testcases = [ (matlab.double([1.0000, 1.0417, 1.0834]), 3, matlab.double([0,1,1]), 366, 3, 2400), #nPerDay = 24, nPerBin = 3
                (matlab.double([1.083, 1.083, 1.125]), 3, matlab.double([1,1,1]), 366, 5, 4000) # nPerBin = 5
                ]
@pytest.mark.parametrize('t, expected_nt, expected_m, expected_EndDOY, expected_nPerBin, expected_nN', testcases)
def test_initializeParameters(matlab_engine, t, expected_nt, expected_m, expected_EndDOY, expected_nPerBin, expected_nN):
    """
    Tests the initializeParameters function in MATLAB.
    """
    nSeasons = 4
    nStrataN = 4
    nBins = 50

    nt, m, EndDOY, nPerBin, nN = matlab_engine.initializeParameters(t, nSeasons, nStrataN, nBins, nargout=5)
    
    assert nt == expected_nt
    assert m == expected_m
    assert EndDOY == expected_EndDOY
    assert nPerBin == expected_nPerBin
    assert nN == expected_nN


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
def test_filterInvalidPoints(matlab_engine, uStar, fNight, NEE, T):
    """
    Test the filterInvalidPoints function in MATLAB.
    """
    
    expected_u_star, expected_valid_annual_indices, expected_num_valid_annual = filter_invalid_points(uStar, fNight, NEE, T)
    expected_u_star, expected_valid_annual_indices, expected_num_valid_annual = \
        matlab.double(expected_u_star.tolist()), matlab.double((expected_valid_annual_indices+1).tolist()), matlab.double(expected_num_valid_annual)
    
    uStar = matlab.double(uStar.tolist())
    fNight = matlab.double(fNight.tolist())
    NEE = matlab.double(NEE.tolist())
    T = matlab.double(T.tolist())

    uStar, itAnnual, ntAnnual = matlab_engine.filterInvalidPoints(uStar, fNight, NEE, T, nargout=3)

    assert np.allclose(uStar, expected_u_star, equal_nan=True)
    assert np.allclose(itAnnual, expected_valid_annual_indices, equal_nan=True)
    assert np.allclose(ntAnnual, expected_num_valid_annual, equal_nan=True)


def test_filterInvalidPoints_logged_data(matlab_engine):
    """
    Test the filterInvalidPoints function in MATLAB.
    """
    artifacts_dir = 'tests/test_artifacts/filterInvalidPoints_artifacts'
    input_names = ['fNight', 'NEE', 'uStar', 'T']
    input_data = {}
    for name in input_names:
        path_to_artifacts = artifacts_dir + f'/CA-Cbo_qca_ustar_2007_0/input_{name}.csv'
        column = pd.read_csv(path_to_artifacts, header=None).iloc[:,0].to_numpy()
        input_data[name] = matlab.double(column.tolist())
    
    expected_output_names = ['uStar', 'itAnnual', 'ntAnnual']
    expected_output_data = {}
    for name in expected_output_names:
        path_to_artifacts = artifacts_dir + f'/CA-Cbo_qca_ustar_2007_0/output_{name}.csv'
        column = pd.read_csv(path_to_artifacts, header=None).iloc[:,0].to_numpy()
        expected_output_data[name] = matlab.double(column.tolist())

    uStar, itAnnual, ntAnnual = matlab_engine.filterInvalidPoints(input_data['uStar'], input_data['fNight'], input_data['NEE'], input_data['T'], nargout=3)

    assert np.allclose(uStar, expected_output_data['uStar'], equal_nan=True)
    assert np.allclose(itAnnual, expected_output_data['itAnnual'], equal_nan=True)
    assert np.allclose(ntAnnual, expected_output_data['ntAnnual'], equal_nan=True)



def test_initializeStatistics(matlab_engine):
    """
    Test the initializeStatistics function in MATLAB initiliazes the Stats2 and Stats3 structures with NaN values.
    """
    nSeasons = 4
    nStrataX = 8

    Stats2, Stats3 = matlab_engine.initializeStatistics(nSeasons, nStrataX, 1, nargout=2)
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
def test_reorderAndPreprocessData(matlab_engine, t, T, uStar, NEE, fNight, EndDOY, m, nt):
    """
    Test the reorderAndPreprocessData function in MATLAB.
    """
    data = [t, T, uStar, NEE, fNight, EndDOY, m, nt]
    
    matlab_data = [matlab.double(d) if not isinstance(d, np.ndarray) else matlab.double(d.tolist()) for d in data ]

    t, T, uStar, NEE, fNight, itAnnual, ntAnnual = matlab_engine.reorderAndPreprocessData(*matlab_data, nargout=7)
    # t = matlab_engine.reorderAndPreprocessData(*matlab_data, nargout=1)
    expected_t, expected_T, expected_uStar, expected_NEE, expected_fNight, expected_itAnnual, expected_ntAnnual = reorder_and_preprocess_data(*data)
    # result = reorder_and_preprocess_data(*data)
    print(T)
    # print(result)
    assert np.allclose(t, expected_t, equal_nan=True)
    assert np.allclose(T, expected_T, equal_nan=True)
    assert np.allclose(uStar, expected_uStar, equal_nan=True)
    assert np.allclose(NEE, expected_NEE, equal_nan=True)
    assert np.allclose(fNight, expected_fNight, equal_nan=True)
    assert np.allclose(itAnnual, expected_itAnnual+1, equal_nan=True) # +1 to match matlab indexings
    assert ntAnnual == expected_ntAnnual


def test_reorderAndPreprocessData_logged_data(matlab_engine):
    """
    Test the reorderAndPreprocessData function in MATLAB.
    """
    artifacts_dir = 'tests/test_artifacts/reorderAndPreprocessData_artifacts'
    input_names = ['t', 'T', 'uStar', 'NEE', 'fNight', 'EndDOY', 'm', 'nt']
    input_data = {}
    for name in input_names:
        path_to_artifacts = artifacts_dir + f'/CA-Cbo_qca_ustar_2007_0/input_{name}.csv'
        column = pd.read_csv(path_to_artifacts, header=None).iloc[:,0].to_numpy()
        if name in {'EndDOY', 'nt'}:
            input_data[name] = matlab.double(int(column[0]))
        else:
            input_data[name] = matlab.double(column.tolist())

    expected_output_names = ['t', 'T', 'uStar', 'NEE', 'fNight', 'itAnnual', 'ntAnnual']
    expected_output_data = {}
    for name in expected_output_names:
        path_to_artifacts = artifacts_dir + f'/CA-Cbo_qca_ustar_2007_0/output_{name}.csv'
        column = pd.read_csv(path_to_artifacts, header=None).iloc[:,0].to_numpy()
        if name == 'ntAnnual':
            expected_output_data[name] = matlab.double(int(column[0]))
        else:
            expected_output_data[name] = matlab.double(column.tolist())
        
    t, T, uStar, NEE, fNight, itAnnual, ntAnnual = matlab_engine.reorderAndPreprocessData(*[input_data[name] for name in input_names], nargout=7)

    assert np.allclose(t, expected_output_data['t'], equal_nan=True)
    assert np.allclose(T, expected_output_data['T'], equal_nan=True)
    assert np.allclose(uStar, expected_output_data['uStar'], equal_nan=True)
    assert np.allclose(NEE, expected_output_data['NEE'], equal_nan=True)
    assert np.allclose(fNight, expected_output_data['fNight'], equal_nan=True)
    assert np.allclose(itAnnual, expected_output_data['itAnnual'], equal_nan=True)
    assert ntAnnual == expected_output_data['ntAnnual'].tomemoryview().tolist()[0][0]


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
def test_computeSeasonIndices(matlab_engine, iSeasons, nSeasons, nPerSeason, ntAnnual, expected_jtSeasons):
    """
    Test the computeSeasonIndices function in MATLAB.
    """
    iSeasons = matlab.double(iSeasons)
    nSeasons = matlab.double(nSeasons)
    nPerSeason = matlab.double(nPerSeason)
    ntAnnual = matlab.double(ntAnnual)

    jtSeasons = matlab_engine.computeSeasonIndices(iSeasons, nSeasons, nPerSeason, ntAnnual)
    jtSeasons = np.array(jtSeasons.tomemoryview().tolist()[0])
    assert np.array_equal(jtSeasons, expected_jtSeasons)
    

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
def test_computeStrataCount(matlab_engine, ntSeason, nPerBin, expected_nStrata):
    """
    Test the computeStrataCount function in MATLAB.
    """
    nStrataX = 8
    nStrataN = 4
    nBins = 50
    ntSeason = matlab.double(ntSeason)
    nPerBin = matlab.double(nPerBin)

    nStrata = matlab_engine.computeStrataCount(ntSeason, nBins, nPerBin, nStrataN, nStrataX)

    assert nStrata == expected_nStrata


def test_computeTemperatureThresholds_logged_data(matlab_engine):
    """
    Test the computeTemperatureTresholds function in MATLAB.
    Tests a single case, function is essentially a wrapper to the matlab percentile function.
    """
    nStrata = 5
    artifacts_dir = 'tests/test_artifacts/computeTemperatureThresholds_artifacts'
    input_names = ['T', 'itSeason']
    input_data = {}
    for name in input_names:
        path_to_artifacts = artifacts_dir + f'/CA-Cbo_qca_ustar_2007_0/input_{name}.csv'
        column = pd.read_csv(path_to_artifacts, header=None).iloc[:,0].to_numpy()
        input_data[name] = matlab.double(column.tolist())

    TTh = matlab_engine.computeTemperatureThresholds(input_data['T'], input_data['itSeason'], nStrata, nargout=1)
    TTh = np.array(TTh.tomemoryview().tolist()[0])
    expected_TTh = artifacts_dir + f'/CA-Cbo_qca_ustar_2007_0/output_TTh.csv'
    expected_TTh = pd.read_csv(expected_TTh, header=None).iloc[0,:].to_numpy()

    assert np.allclose(TTh, expected_TTh)

tetcases = [
    (rng.uniform(-20,20,1000), np.array(rng.choice(1000, size=500, replace=False)), [-14.601,-5.22904,-2.095605,1.836835,5.136015,14.2835], 0), # Nominal case
    (np.array([-20, -19, -15, 1, 4 ,14, 8, 7, 8 ,4], dtype=float), np.array([0, 1, 2]), [-14.601,-5.22904,-2.095605,1.836835,5.136015,14.2835], 1), # # No matching indices
    (np.array([-1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], dtype=float), np.array([4, 7, 9]), [1, 1, 1, 1, 1, 1], 4), # Non increasing threshold TTH 
    (rng.uniform(-5,25,900), np.array(rng.choice(1000, size=300, replace=False)), [-1.34166,5.217795,8.340625,12.45965,16.9017,24.672], 2), # iStrata = 2
    (rng.uniform(0,30,400), np.array(rng.choice(1000, size=200, replace=False)), [2.34335,6.89097,11.09125,14.6745,17.95015,27.262], 4), # iStrata = 4
    (rng.uniform(-5,15,800), np.array(rng.choice(1000, size=400, replace=False)), [-2.22904,0.904395,4.836835,8.136015,13.2835], 3), # iStrata = 3, length(TTh) = 5

]
@pytest.mark.parametrize('T, itSeason, TTh, iStrata', tetcases)
def test_findStratumIndices(matlab_engine, T, itSeason, TTh, iStrata):
    """
    Test the findStratumIndices function in MATLAB.
    """

    mask = (T >= TTh[iStrata]) & (T <= TTh[iStrata + 1])
    # Extract the indices where the condition is true
    itStrata = mask.nonzero()
    # print(itStrata)

    # Intersect the selected indices with itSeason
    expected_itStrata = np.intersect1d(itStrata, itSeason) + 1
    print(expected_itStrata)

    T = matlab.double(T)
    itSeason = matlab.double(np.array(itSeason+1, dtype=float))
    TTh = matlab.double(TTh)
    iStrata = iStrata + 1

    itStrata = matlab_engine.findStratumIndices(T, itSeason, TTh, iStrata, nargout=1)
    
    itStrata = np.array(itStrata.tomemoryview().tolist()[0], dtype=int)
    print(itStrata)

    assert np.array_equal(itStrata, expected_itStrata)
    # assert 1==0


def test_addStatisticsFields(matlab_engine):
    """
    Test the addStatistics function in MATLAB.
    """

    # Generate input data
    rng = np.random.default_rng()
    xs_keys = ['n', 'Cp', 'Fmax', 'p', 'b0', 'b1', 'b2', 'c2', 'cib0', 'cib1', 'cic2', 'mt' , 'ti', 'tf', 'ruStarVsT', 'puStarVsT', 'mT', 'ciT']
    xs = {key:np.nan for key in xs_keys}
    t = np.linspace(0, 10, 500)
    r = [[1, 0.429039265010557],[0.429039265010557, 1]]
    p = [[1, 0.00120739842384987], [0.00120739842384987, 1]]
    T = rng.uniform(-20,20,1000)
    itStrata = np.array(list(range(1,51)) + list(range(200,300)))

    xs = matlab_engine.addStatisticsFields(xs, matlab.double(t.tolist()), matlab.double(r), matlab.double(p), matlab.double(T.tolist()), matlab.double((itStrata+1).tolist()), nargout=1)
    expected_xs = {}
    expected_xs = addStatisticsFields(expected_xs, t, T, r, p, itStrata)

    output_xs = np.array([xs['mt'], xs['ti'], xs['tf'], xs['ruStarVsT'], xs['puStarVsT'], xs['mT'], xs['ciT']])
    
    assert np.allclose(list(expected_xs.values()), output_xs, equal_nan=True)

