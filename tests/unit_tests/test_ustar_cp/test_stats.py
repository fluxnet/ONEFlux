import pytest
import numpy as np

nan = np.nan

# Define the expected field names for StatsMT
expected_fields = ['n', 'Cp', 'Fmax', 'p', 'b0', 'b1', 'b2', 'c2', 'cib0', 'cib1', 'cic2',
    'mt', 'ti', 'tf', 'ruStarVsT', 'puStarVsT', 'mT', 'ciT'
]

# Test for the generate_statsMT function
def test_generate_statsMT(test_engine):
    # Generate the StatsMT struct
    StatsMT = test_engine.generate_statsMT()

    # Ensure all expected fields exist and are NaN
    for field in expected_fields:
        assert field in StatsMT, f"Missing field: {field}"  # Access fields like dict keys
        assert np.isnan(StatsMT[field]), f"Field {field} is not NaN"

# TODO: remove differential tests
stats_entry = {'n': nan, 'Cp': nan, 'Fmax': nan, 'p': nan, 'b0': nan, 'b1': nan, 'b2': nan, 'c2': nan, 'cib0': nan, 'cib1': nan, 'cic2': nan, 'mt': nan, 'ti': nan, 'tf': nan, 'ruStarVsT': nan, 'puStarVsT': nan, 'mT': nan, 'ciT': nan}
# Test for the setup_Stats function
@pytest.mark.parametrize(
    "nBoot, nSeasons, nStrataX, expected_shape",
    [
        # Case 1: Basic 2x2x2 array
        (2, 2, 2, ([[[stats_entry, stats_entry],[stats_entry,stats_entry]],[[stats_entry,stats_entry],[stats_entry,stats_entry]]])),

        # TODO: check whether we need these tests
        # Case 2a: Single season, single strata, single boot
        #(1, 1, 1, stats_entry),

        # Case 3: No bootstrap iterations (nBoot=0)
        #(0, 2, 3, stats_entry),
    ]
)
def test_setup_Stats_differential(test_engine, nBoot, nSeasons, nStrataX, expected_shape):
    # Call the MATLAB function
    Stats= test_engine.setup_Stats(nBoot, nSeasons, nStrataX, jsonencode=[0])

    assert test_engine.equal(Stats, expected_shape)

    # Call the python function
    import oneflux_steps.ustar_cp_python.cpdBootstrap as cpdBootstrap
    Stats_python = cpdBootstrap.setup_Stats(nBoot, nSeasons, nStrataX)

    assert_dicts_with_nan_equal(Stats_python, expected_shape)

def assert_dicts_with_nan_equal(obj1, obj2) -> None:
    """
    Recursively assert equality between dictionaries, lists of dictionaries, or nested lists containing dictionaries,
    considering NaN values.

    Args:
        obj1 (Any): First object (dict, list, or nested structure).
        obj2 (Any): Second object (dict, list, or nested structure).

    Raises:
        AssertionError: If the objects or nested contents are not equal.
    """
    if isinstance(obj1, dict) and isinstance(obj2, dict):
        assert obj1.keys() == obj2.keys(), "Dictionaries have different keys."
        for key in obj1:
            val1, val2 = obj1[key], obj2[key]
            if isinstance(val1, float) and isinstance(val2, float):
                assert np.isnan(val1) and np.isnan(val2) or val1 == val2, f"Mismatch at key {key}: {val1} != {val2}"
            else:
                assert_dicts_with_nan_equal(val1, val2)

    elif isinstance(obj1, list) and isinstance(obj2, list):
        assert len(obj1) == len(obj2), "Lists have different lengths."
        for item1, item2 in zip(obj1, obj2):
            assert_dicts_with_nan_equal(item1, item2)

    else:
        assert obj1 == obj2, f"Mismatch in items: {obj1} != {obj2}"