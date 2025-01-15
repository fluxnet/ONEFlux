import pytest
import numpy as np

# 1. test_cpdFmax2pCp3
testcases_cpdFmax2pCp3 = [
    (np.nan, 52, np.nan, "Case 1: Input values are NaN"),
    (42, np.nan, np.nan, "Case 2: Different input value is NaN"),
    (3.14159265358979323, 9, np.nan, "Case 3: n < 10"),
    (5.45204127574611, 52, 0.384643400326067, "Case 4: Below f-critical(1)"),
    (17, 53, 0.005441758015001463, "Case 5: Above f-critical(3)"),
    (10, 52, 0.0761404222166437, "Case 6: Between f-critical(1) and f-critical(3)"),
    (0, 55, 1.0, "Case 7: fmax = 0"),
    (1.6301, 52, 1.0, "Case 8: fmax = fcritical(1)"),
    (2.37324492970613, 55, 1.0, "Case 9: Nominal scenario 1"),
    (10.3567400792636, 54, 0.0657053181314848, "Case 10: Nominal scenario 2"),
]

@pytest.mark.parametrize("fmax, n, expected_p3, description", testcases_cpdFmax2pCp3)
def test_cpdFmax2pCp3(test_engine, fmax, n, expected_p3, description):
    # Convert input
    fmax = test_engine.convert(fmax)
    n = test_engine.convert(n)

    # Run the function
    output_p3 = test_engine.cpdFmax2pCp3(fmax, n)

    # Assertion
    assert test_engine.equal(test_engine.convert(output_p3), expected_p3), description

# 2. test_calculate_p_high
testcases_calculate_p_high = [
    (20, 15, 50, 0.0018068999227986993, "Case 1: Fmax > FmaxCritical_high, typical scenario"),
    (15, 15, 50, 0.010000000000000009, "Case 2: Fmax = FmaxCritical_high, boundary condition"),
    (15.1, 15, 50, 0.00965419741276663, "Case 3: Fmax slightly above FmaxCritical_high"),
    (30, 15, 100, 4.4960217949308046e-05, "Case 4: Larger difference, Fmax >> FmaxCritical_high"),
    (np.nan, 15, 50, 0, "Case 5: Fmax is NaN, expect p=0"),
    (20, np.nan, 50, 0, "Case 6: FmaxCritical_high is NaN, expect p=0"),
    (20, 15, np.nan, 0, "Case 7: n is NaN, expect p=0"),
    (20, 0, 50, 0, "Case 8: FmaxCritical_high=0, invalid, expect p=0"),
    (-20, 15, 50, 2.0, "Case 9: Negative Fmax, expect p=2.0"),
    (20, -15, 50, 2.0, "Case 10: Negative FmaxCritical_high, expect p=2.0"),
    (20, 15, -50, 0, "Case 11: Negative n, expect p=0"),
]

@pytest.mark.parametrize("Fmax, FmaxCritical_high, n, expected_p, description", testcases_calculate_p_high)
def test_calculate_p_high(test_engine, Fmax, FmaxCritical_high, n, expected_p, description):
    Fmax = test_engine.convert(Fmax)
    FmaxCritical_high = test_engine.convert(FmaxCritical_high)
    n = test_engine.convert(n)

    result = test_engine.calculate_p_high(Fmax, FmaxCritical_high, n)

    assert test_engine.equal(test_engine.convert(result), expected_p), description


# 3. test_calculate_p_interpolate
testcases_calculate_p_interpolate = [
    (10, [5, 15], [0.1, 0.05], 0.925, 
     "Case 1: Fmax between FmaxCritical[0] & FmaxCritical[1], expect interpolated p"),
    (15, [10, 15, 20], [0.1, 0.05, 0.01], 0.95, 
     "Case 2: Fmax = FmaxCritical[1], direct match"),
    (17, [15, 20], [0.05, 0.01], 0.966, 
     "Case 3: Fmax between FmaxCritical[0] & FmaxCritical[1], expect interpolation"),
    (4, [5, 10, 15], [0.1, 0.05, 0.01], 0.8888266666666668, 
     "Case 4: Fmax < min(FmaxCritical), special behavior"),
    (16, [5, 10, 15], [0.1, 0.05, 0.01], 0.9967733333333333, 
     "Case 5: Fmax > max(FmaxCritical), special behavior"),
    (np.nan, [5, 10, 15], [0.1, 0.05, 0.01], np.nan, 
     "Case 6: Fmax is NaN, expect NaN"),
]

@pytest.mark.parametrize("Fmax, FmaxCritical, pTable, expected_p, description", testcases_calculate_p_interpolate)
def test_calculate_p_interpolate(test_engine, Fmax, FmaxCritical, pTable, expected_p, description):
    Fmax = test_engine.convert(Fmax)
    FmaxCritical = test_engine.convert(FmaxCritical)
    pTable = test_engine.convert(pTable)

    result = test_engine.calculate_p_interpolate(Fmax, FmaxCritical, pTable)

    assert test_engine.equal(result, test_engine.convert(expected_p)), description


# 4. test_calculate_p_low
testcases_calculate_p_low = [
    (5.0, 10.0, 30, 0.4898436922743534, "Case 1: Basic test with Fmax < FmaxCritical_low"),
    (0.0, 10.0, 30, 1.0, "Case 2: Fmax = 0"),
    (5.0, 10.0, 3, 0.239649936459168, "Case 3: Small sample size n=3"),
    (10.0, 10.0, 30, 0.09999999999999987, "Case 4: Fmax = FmaxCritical_low"),
    (np.nan, 10.0, 30, 1.0, "Case 5: Fmax is NaN, expect p=1.0"),
    (5.0, np.nan, 30, 1.0, "Case 6: FmaxCritical_low is NaN, expect p=1.0"),
    (5.0, 10.0, 0, 1.0, "Case 7: n=0, invalid, expect p=1.0"),
    (5.0, 0.0, 30, 0.0, "Case 8: FmaxCritical_low=0.0, invalid, expect p=0.0"),
]

@pytest.mark.parametrize("Fmax, FmaxCritical_low, n, expected_p, description", testcases_calculate_p_low)
def test_calculate_p_low(test_engine, Fmax, FmaxCritical_low, n, expected_p, description):
    Fmax = test_engine.convert(Fmax)
    FmaxCritical_low = test_engine.convert(FmaxCritical_low)
    n = test_engine.convert(n)

    result = test_engine.calculate_p_low(Fmax, FmaxCritical_low, n)

    assert test_engine.equal(test_engine.convert(result), expected_p), description


# 5. test_interpolate_FmaxCritical
testcases_interpolate_FmaxCritical = [
    (
        15, 
        [10, 20, 30],
        [[5, 10, 15], [6, 12, 18], [7, 14, 21]],
        [5.5, 11, 16.5],
        "Case 1: Interpolation within range of nTable"
    ),
    (
        10, 
        [10, 20, 30],
        [[5, 10, 15], [6, 12, 18], [7, 14, 21]],
        [5, 10, 15],
        "Case 2: Exact match in nTable, no interpolation needed"
    ),
    (
        5, 
        [10, 20, 30],
        [[5, 10, 15], [6, 12, 18], [7, 14, 21]],
        [4.5, 9.0, 13.5],
        "Case 3: n below nTable range, custom behavior"
    ),
    (
        35, 
        [10, 20, 30],
        [[5, 10, 15], [6, 12, 18], [7, 14, 21]],
        [7.5, 15.0, 22.5],
        "Case 4: n above nTable range, custom behavior"
    ),
]

@pytest.mark.parametrize(
    "n, nTable, FmaxTable, expected_FmaxCritical, description", 
    testcases_interpolate_FmaxCritical
)
def test_interpolate_FmaxCritical(n, nTable, FmaxTable, expected_FmaxCritical, description, test_engine):
    n = test_engine.convert(n)
    nTable = test_engine.convert(nTable)
    FmaxTable = test_engine.convert(FmaxTable)

    result = test_engine.interpolate_FmaxCritical(n, nTable, FmaxTable)

    assert test_engine.equal(test_engine.convert(expected_FmaxCritical), result), description
