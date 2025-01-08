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
def test_filterInvalidPoints_differential(test_engine, uStar, fNight, NEE, T):
    """
    Test the filterInvalidPoints function.
    """
    
    expected_u_star, expected_valid_annual_indices, expected_num_valid_annual = filterInvalidPoints(uStar, fNight, NEE, T)
    # 'to_matlab' optional argument to account for 1-based indexing in MATLAB
    expected_u_star, expected_valid_annual_indices, expected_num_valid_annual = \
        test_engine.convert(expected_u_star), test_engine.convert(expected_valid_annual_indices, 'to_matlab'), test_engine.convert(expected_num_valid_annual) 
    
    uStar = test_engine.convert(uStar)
    fNight = test_engine.convert(fNight)
    NEE = test_engine.convert(NEE)
    T = test_engine.convert(T)

    uStar, itAnnual, ntAnnual = test_engine.filterInvalidPoints(uStar, fNight, NEE, T, nargout=3)

    assert test_engine.equal(test_engine.convert(uStar), expected_u_star)
    assert test_engine.equal(test_engine.convert(itAnnual), expected_valid_annual_indices)
    assert test_engine.equal(test_engine.convert(ntAnnual), expected_num_valid_annual)


occurrences = 50
size = 600
testcases = [
               (rng.uniform(0,5,size), rng.uniform(0,5,size), rng.uniform(0,5,size), rng.uniform(0,5,size), np.random.randint(0,2,size), 366, np.repeat(np.arange(1, 13), occurrences), size), # Nominal case
                (rng.uniform(0,5,size), rng.uniform(0,5,size), rng.uniform(0,5,size), rng.uniform(0,5,size), np.ones(size), 366, np.repeat(np.arange(1, 13), occurrences), size), # All nighttime data
                (rng.uniform(0,5,size), rng.uniform(0,5,size), rng.uniform(0,5,size), rng.uniform(0,5,size), np.zeros(size), 366, np.repeat(np.arange(1, 13), occurrences), size) # All daytime data
             ]
@pytest.mark.parametrize('t, T, uStar, NEE, fNight, EndDOY, m, nt', testcases)
def test_reorderAndPreprocessData_differential(test_engine, t, T, uStar, NEE, fNight, EndDOY, m, nt):
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
    # 'to_matlab' optional argument to account for 1-based indexing in MATLAB
    assert test_engine.equal(test_engine.convert(itAnnual), test_engine.convert(expected_itAnnual, 'to_matlab')) # +1 to match matlab indexings
    assert test_engine.equal(ntAnnual, expected_ntAnnual)


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
def test_computeSeasonIndices_differential(test_engine, iSeasons, nSeasons, nPerSeason, ntAnnual, expected_jtSeasons):
    """
    Test the computeSeasonIndices function.
    """

    python_jtSeasons = computeSeasonIndices(iSeasons, nSeasons, nPerSeason, ntAnnual)

    jtSeasons = test_engine.computeSeasonIndices(iSeasons, nSeasons, nPerSeason, test_engine.convert(ntAnnual))


    assert test_engine.equal(test_engine.convert(jtSeasons), test_engine.convert(expected_jtSeasons))
    assert test_engine.equal(test_engine.convert(python_jtSeasons), expected_jtSeasons)
    

tetcases = [
    (rng.uniform(-20,20,1000), np.array(rng.choice(1000, size=500, replace=False)), [-14.601,-5.22904,-2.095605,1.836835,5.136015,14.2835], 0), # Nominal case
    (np.array([-20, -19, -15, 1, 4 ,14, 8, 7, 8 ,4], dtype=float), np.array([0, 1, 2]), [-14.601,-5.22904,-2.095605,1.836835,5.136015,14.2835], 1), # # No matching indices
    (np.array([-1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], dtype=float), np.array([4, 7, 9]), [1, 1, 1, 1, 1, 1], 4), # Non increasing threshold TTH 
    (rng.uniform(-5,25,900), np.array(rng.choice(1000, size=300, replace=False)), [-1.34166,5.217795,8.340625,12.45965,16.9017,24.672], 2), # iStrata = 2
    (rng.uniform(0,30,400), np.array(rng.choice(1000, size=200, replace=False)), [2.34335,6.89097,11.09125,14.6745,17.95015,27.262], 4), # iStrata = 4
    (rng.uniform(-5,15,800), np.array(rng.choice(1000, size=400, replace=False)), [-2.22904,0.904395,4.836835,8.136015,13.2835], 3), # iStrata = 3, length(TTh) = 5

]
@pytest.mark.parametrize('T, itSeason, TTh, iStrata', tetcases)
def test_findStratumIndices_differential(test_engine, T, itSeason, TTh, iStrata):
    """
    Test the findStratumIndices function.
    """
    expected_itStrata = findStratumIndices(T, itSeason, TTh, iStrata)

    T = test_engine.convert(T)
    # 'to_matlab' optional argument to account for 1-based indexing in MATLAB
    itSeason = test_engine.convert(np.array(itSeason, dtype=float), 'to_matlab') # +1 to account for 1-based indexing in MATLAB
    TTh = test_engine.convert(TTh)
    iStrata = test_engine.convert(iStrata, 'to_matlab') # +1 to account for 1-based indexing in MATLAB

    itStrata = test_engine.findStratumIndices(T, itSeason, TTh, iStrata, nargout=1)
    assert test_engine.equal(itStrata, test_engine.convert(expected_itStrata, 'to_matlab')) # +1 to account for 1-based indexing in matlab


def test_addStatisticsFields_differential(test_engine):
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
    # 'to_matlab' optional argument to account for 1-based indexing in MATLAB
    xs = test_engine.addStatisticsFields(xs, test_engine.convert(t), test_engine.convert(r), \
                                          test_engine.convert(p), test_engine.convert(T), test_engine.convert(itStrata, 'to_matlab'), nargout=1)
    print("test_engine output: ",xs)
    expected_xs = {}
    expected_xs = addStatisticsFields(expected_xs, t, r, p, T, itStrata)

    output_xs = np.array([xs['mt'], xs['ti'], xs['tf'], xs['ruStarVsT'], xs['puStarVsT'], xs['mT'], xs['ciT']])
    print(output_xs)
    print(expected_xs)    
    assert test_engine.equal(test_engine.convert(list(expected_xs.values())), output_xs)

