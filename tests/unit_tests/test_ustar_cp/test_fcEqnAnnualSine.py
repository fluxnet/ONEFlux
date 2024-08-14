# Define a function to convert inputs to MATLAB arrays
def to_matlab_array(arr):
    return matlab.double(arr.tolist())

# Define the function to test the MATLAB function
def test_fcEqnAnnualSine():
    # Define test cases with known expected outputs
    test_cases = [
        {
            "b": [1, 2, 3],
            "t": [1, 2, 3, 4, 5],
            "expected": [1 + 2 * np.sin(2 * np.pi / 365.25 * (t - 3)) for t in [1, 2, 3, 4, 5]]
        },
        {
            "b": [0, 1, 0],
            "t": [10, 20, 30],
            "expected": [0 + 1 * np.sin(2 * np.pi / 365.25 * (t - 0)) for t in [10, 20, 30]]
        },
        {
            "b": [5, -3, 12],
            "t": [100, 200, 300],
            "expected": [5 - 3 * np.sin(2 * np.pi / 365.25 * (t - 12)) for t in [100, 200, 300]]
        }
    ]

    for case in test_cases:
        b = to_matlab_array(np.array(case["b"]))
        t = to_matlab_array(np.array(case["t"]))
        expected = np.array(case["expected"])

        # Call the MATLAB function
        y = np.array(eng.fcEqnAnnualSine(b, t))

        # Check if the output matches the expected values
        np.testing.assert_almost_equal(y, expected, decimal=5, err_msg=f"Failed for b={case['b']} and t={case['t']}")
