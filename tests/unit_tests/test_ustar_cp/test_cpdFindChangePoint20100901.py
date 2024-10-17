import pytest
import matlab.engine
import numpy as np

@pytest.fixture
def test_data():
    # Generate synthetic data with change points
    xx = np.linspace(0, 10, 101)
    yy = np.piecewise(xx, [xx < 3, (xx >= 3) & (xx < 7), xx >= 7],
                      [lambda x: 2 * x + 1, lambda x: -x + 10, lambda x: 0.5 * x - 0.5])
    return xx, yy

def test_cpdFindChangePoint20100901(matlab_engine, test_data):
    # Define test inputs
    xx, yy = test_data
    fPlot = 0
    cPlot = 'Test Plot'

    # Call the MATLAB function
    Cp2, s2, Cp3, s3 = matlab_engine.cpdFindChangePoint20100901(xx, yy, fPlot, cPlot, nargout=4)

    # Perform assertions
    assert isinstance(Cp2, float)
    assert isinstance(Cp3, float)
    assert isinstance(s2, dict)
    assert isinstance(s3, dict)

    # Check the structure of s2 and s3
    for s in [s2, s3]:
        assert isinstance(s['n'], float)
        assert isinstance(s['Cp'], float)
        assert isinstance(s['Fmax'], float)
        assert isinstance(s['p'], float)
        assert isinstance(s['b0'], float)
        assert isinstance(s['b1'], float)
        assert isinstance(s['b2'], float)
        assert isinstance(s['c2'], float)
        assert isinstance(s['cib0'], float)
        assert isinstance(s['cib1'], float)
        assert isinstance(s['cic2'], float)

    # Additional checks can be added based on expected output
    assert s2['n'] == len(xx)
    assert s3['n'] == len(xx)
    assert Cp2 == 1.8
    assert Cp3 == 2.6

if __name__ == "__main__":
    pytest.main()