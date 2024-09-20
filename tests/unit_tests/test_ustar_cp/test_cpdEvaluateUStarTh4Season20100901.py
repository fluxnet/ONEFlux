import pytest
import matlab.engine
import numpy as np

@pytest.fixture(scope="module")
def matlab_engine():
    eng = matlab.engine.start_matlab()
    eng.addpath('/home/tcai/Projects/ONEFlux/oneflux_steps/ustar_cp')
    yield eng
    eng.quit()

def test_cpdEvaluateUStarTh4Season20100901(matlab_engine):
    # Define test inputs
    t = matlab.double(np.linspace(1, 365, 365).tolist())
    NEE = matlab.double(np.random.rand(365).tolist())
    uStar = matlab.double(np.random.rand(365).tolist())
    T = matlab.double(np.random.rand(365).tolist())
    fNight = matlab.double(np.random.randint(0, 2, 365).tolist())
    fPlot = 0
    cSiteYr = 'TestSiteYear'

    # Call the MATLAB function
    Cp2, Stats2, Cp3, Stats3 = matlab_engine.cpdEvaluateUStarTh4Season20100901(
        t, NEE, uStar, T, fNight, fPlot, cSiteYr, nargout=4
    )

    # Perform assertions
    assert isinstance(Cp2, matlab.double)
    assert isinstance(Stats2, matlab.struct)
    assert isinstance(Cp3, matlab.double)
    assert isinstance(Stats3, matlab.struct)

    # Additional checks can be added based on expected output
    assert len(Cp2) == 4  # Assuming nSeasons = 4
    assert len(Cp3) == 4  # Assuming nSeasons = 4

    # Check the structure of Stats2 and Stats3
    for i in range(4):  # Assuming nSeasons = 4
        for j in range(8):  # Assuming nStrataX = 8
            assert 'n' in Stats2[i][j]
            assert 'Cp' in Stats2[i][j]
            assert 'Fmax' in Stats2[i][j]
            assert 'p' in Stats2[i][j]
            assert 'b0' in Stats2[i][j]
            assert 'b1' in Stats2[i][j]
            assert 'b2' in Stats2[i][j]
            assert 'c2' in Stats2[i][j]
            assert 'cib0' in Stats2[i][j]
            assert 'cib1' in Stats2[i][j]
            assert 'cic2' in Stats2[i][j]
            assert 'mt' in Stats2[i][j]
            assert 'ti' in Stats2[i][j]
            assert 'tf' in Stats2[i][j]
            assert 'ruStarVsT' in Stats2[i][j]
            assert 'puStarVsT' in Stats2[i][j]
            assert 'mT' in Stats2[i][j]
            assert 'ciT' in Stats2[i][j]

            assert 'n' in Stats3[i][j]
            assert 'Cp' in Stats3[i][j]
            assert 'Fmax' in Stats3[i][j]
            assert 'p' in Stats3[i][j]
            assert 'b0' in Stats3[i][j]
            assert 'b1' in Stats3[i][j]
            assert 'b2' in Stats3[i][j]
            assert 'c2' in Stats3[i][j]
            assert 'cib0' in Stats3[i][j]
            assert 'cib1' in Stats3[i][j]
            assert 'cic2' in Stats3[i][j]
            assert 'mt' in Stats3[i][j]
            assert 'ti' in Stats3[i][j]
            assert 'tf' in Stats3[i][j]
            assert 'ruStarVsT' in Stats3[i][j]
            assert 'puStarVsT' in Stats3[i][j]
            assert 'mT' in Stats3[i][j]
            assert 'ciT' in Stats3[i][j]

if __name__ == "__main__":
    pytest.main()