# test_cpdBootstrapUStarTh4Season20100901_modular.py

import pytest
import numpy as np
import matlab
import math

def test_initialize_bootstrap(matlab_engine):
    """
    Test the initializeBootstrap function to ensure it correctly initializes variables.
    """
    # Example input data
    t = matlab.double(np.linspace(0, 100, 4800).tolist())  # Time vector
    NEE = matlab.double(np.random.randn(4800).tolist())    # NEE data
    uStar = matlab.double(np.random.uniform(0, 2, 4800).tolist())  # uStar data
    T = matlab.double(np.random.uniform(-10, 30, 4800).tolist())    # Temperature data
    fNight = matlab.logical(np.zeros(4800, dtype=bool).tolist())    # Nighttime flag
    nBoot = 5

    # Call the MATLAB function
    Cp2, Cp3, Stats2, Stats3, StatsMT, nt, nPerDay, ntNee, ntN = matlab_engine.initializeBootstrap(t, NEE, uStar, T, fNight, nBoot, nargout=9)

    # Assertions to ensure correct initialization
    assert isinstance(Cp2, matlab.double) and np.isnan(Cp2).all()
    assert isinstance(Cp3, matlab.double) and np.isnan(Cp3).all()
    assert isinstance(Stats2, matlab.struct)
    assert isinstance(Stats3, matlab.struct)
    assert isinstance(nt, float)
    assert isinstance(nPerDay, float)
    assert isinstance(ntNee, float)
    assert isinstance(ntN, float)

def test_initialize_stats_mt(matlab_engine):
    """
    Test the initializeStatsMT function to ensure it correctly initializes a Stats structure.
    """
    # Call the MATLAB function
    StatsMT = matlab_engine.initializeStatsMT(nargout=1)

    # Assertions to ensure correct structure initialization
    assert StatsMT.n is np.nan
    assert StatsMT.Cp is np.nan
    assert StatsMT.Fmax is np.nan
    assert StatsMT.p is np.nan
    assert StatsMT.b0 is np.nan
    assert StatsMT.b1 is np.nan
    assert StatsMT.b2 is np.nan
    assert StatsMT.c2 is np.nan
    assert StatsMT.cib0 is np.nan
    assert StatsMT.cib1 is np.nan
    assert StatsMT.cic2 is np.nan
    assert StatsMT.mt is np.nan
    assert StatsMT.ti is np.nan
    assert StatsMT.tf is np.nan
    assert StatsMT.ruStarVsT is np.nan
    assert StatsMT.puStarVsT is np.nan
    assert StatsMT.mT is np.nan
    assert StatsMT.ciT is np.nan

def test_perform_bootstrap_iteration(matlab_engine):
    """
    Test the performBootstrapIteration function to ensure it correctly performs a single iteration.
    """
    # Example input data
    t = matlab.double(np.linspace(0, 100, 4800).tolist())  # Time vector
    NEE = matlab.double(np.random.randn(4800).tolist())    # NEE data
    uStar = matlab.double(np.random.uniform(0, 2, 4800).tolist())  # uStar data
    T = matlab.double(np.random.uniform(-10, 30, 4800).tolist())    # Temperature data
    fNight = matlab.logical(np.zeros(4800, dtype=bool).tolist())    # Nighttime flag
    fPlot = False
    cSiteYr = 'TestSite_2024'
    iBoot = 1
    nt = 4800
    ntNee = 4800

    # Call the MATLAB function
    Cp2, Stats2, Cp3, Stats3 = matlab_engine.performBootstrapIteration(t, NEE, uStar, T, fNight, fPlot, cSiteYr, iBoot, nt, ntNee, nargout=4)

    # Assertions to ensure correct iteration
    assert isinstance(Cp2, matlab.double)
    assert isinstance(Cp3, matlab.double)
    assert isinstance(Stats2, matlab.struct)
    assert isinstance(Stats3, matlab.struct)
    assert Cp2.size == 32  # 4 seasons * 8 strata
    assert Cp3.size == 32  # 4 seasons * 8 strata

def test_cpdBootstrapUStarTh4Season20100901_full_execution(matlab_engine):
    """
    Test the full execution of cpdBootstrapUStarTh4Season20100901 to ensure it integrates correctly.
    """
    # Example input data
    t = matlab.double(np.linspace(0, 100, 4800).tolist())  # Time vector
    NEE = matlab.double(np.random.randn(4800).tolist())    # NEE data
    uStar = matlab.double(np.random.uniform(0, 2, 4800).tolist())  # uStar data
    T = matlab.double(np.random.uniform(-10, 30, 4800).tolist())    # Temperature data
    fNight = matlab.logical(np.zeros(4800, dtype=bool).tolist())    # Nighttime flag
    fPlot = False
    cSiteYr = 'TestSite_2024'
    nBoot = 5

    # Call the MATLAB function
    Cp2, Stats2, Cp3, Stats3 = matlab_engine.cpdBootstrapUStarTh4Season20100901(t, NEE, uStar, T, fNight, fPlot, cSiteYr, nBoot, nargout=4)

    # Assertions to ensure correct execution
    assert isinstance(Cp2, matlab.double)
    assert isinstance(Cp3, matlab.double)
    assert isinstance(Stats2, matlab.struct)
    assert isinstance(Stats3, matlab.struct)
    assert Cp2.size == 32 * nBoot  # 4 seasons * 8 strata * nBoot
    assert Cp3.size == 32 * nBoot  # 4 seasons * 8 strata * nBoot
