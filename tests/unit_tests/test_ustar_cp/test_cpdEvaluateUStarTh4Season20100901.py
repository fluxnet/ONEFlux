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


def json_to_numpy(data):
    
    all_arrays = []
    for record_group in data:  # Handle nested lists in the JSON
        group_arrays = []
        for record in record_group:
            array = np.array(list(record.values()), dtype=float)  # Convert to numpy array
            group_arrays.append(array)
        all_arrays.append(np.array(group_arrays))  # Group into a 2D array for each group
    return np.array(all_arrays)


cpdEvaluateUStar_test_cases = ['2007', '2007_fnight_zero_0']
@pytest.mark.parametrize('year', cpdEvaluateUStar_test_cases)
def test_cpdEvaluateUStarTh4Season20100901(matlab_engine, year): # This test stores the logged data as row major instead of column major
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


def test_filterInvalidPoints(matlab_engine):
    """
    Test the filterInvalidPoints function in MATLAB.
    """
    artifacts_dir = 'tests/test_artifacts/filterInvalidPoints_artifacts'
    input_names = ['fNight', 'NEE', 'uStar', 'T']
    input_data = {}
    for name in input_names:
        path_to_artifacts = artifacts_dir + f'/CA-Cbo_qca_ustar_2007_0/input_{name}.csv'
        column = pd.read_csv(path_to_artifacts, header=None).iloc[:,0].to_numpy()
        #print(column)
        if name == 'fNight':
            input_data[name] = matlab.int8(column.tolist())
        else:
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
    Test the initializeStatistics function in MATLAB.
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




    


