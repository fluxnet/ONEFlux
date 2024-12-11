import pytest
import matlab.engine
import numpy as np

@pytest.fixture
def sample_stats_json(matlab_engine):
    """Create a JSON-encoded single-entry MATLAB-compatible stats struct."""
    stats_entry = {
        "n": 1.0, "Cp": float("nan"), "Fmax": float("nan"), "p": float("nan"),
        "b0": float("nan"), "b1": float("nan"), "b2": float("nan"), "c2": float("nan"),
        "cib0": float("nan"), "cib1": float("nan"), "cic2": float("nan"),
        "mt": float("nan"), "ti": float("nan"), "tf": float("nan"),
        "ruStarVsT": float("nan"), "puStarVsT": float("nan"),
        "mT": float("nan"), "ciT": float("nan")
    }
    return matlab_engine.jsonencode(stats_entry)

@pytest.fixture
def multi_stats_json(matlab_engine):
    """Create a multi-entry JSON representation of the stats structure."""
    stats_entry = {
        "n": 1.0, "Cp": float("nan"), "Fmax": float("nan"), "p": float("nan"),
        "b0": float("nan"), "b1": float("nan"), "b2": float("nan"), "c2": float("nan"),
        "cib0": float("nan"), "cib1": float("nan"), "cic2": float("nan"),
        "mt": float("nan"), "ti": float("nan"), "tf": float("nan"),
        "ruStarVsT": float("nan"), "puStarVsT": float("nan"),
        "mT": float("nan"), "ciT": float("nan")
    }

    multi_stats = [[[stats_entry, stats_entry], [stats_entry, stats_entry]], 
                   [[stats_entry, stats_entry], [stats_entry, stats_entry]]]
    return matlab_engine.jsonencode(multi_stats)

@pytest.mark.parametrize(
    "field_name, expected",
    [
        ("n", [[1.0]]), 
        ("Cp", [[np.nan]])
    ]
)
def test_fcReadFields_valid(matlab_engine, sample_stats_json, field_name, expected):
    """Test fcReadFields with a single-entry JSON."""
    result = matlab_engine.fcReadFields(sample_stats_json, field_name, 'jsondecode', 1)
    assert np.allclose(result, expected, equal_nan=True), f"Expected {expected}, got {result}"

@pytest.mark.parametrize(
    "field_name, expected",
    [
        ("n", [[[1.0, 1.0], [1.0, 1.0]], [[1.0, 1.0], [1.0, 1.0]]]),
        ("Cp", [[[np.nan, np.nan], [np.nan, np.nan]], 
                [[np.nan, np.nan], [np.nan, np.nan]]]),
    ]
)
def test_fcReadFields_multi(matlab_engine, multi_stats_json, field_name, expected):
    """Test fcReadFields with a multi-entry JSON."""
    result = matlab_engine.fcReadFields(multi_stats_json, field_name, 'jsondecode', 1)

    # Convert MATLAB result
    if isinstance(result, matlab.double):
        result_list = [[[float(cell) if not np.isnan(cell) else float("nan") 
                         for cell in row] for row in layer] for layer in result]
    else:
        pytest.fail(f"Unexpected MATLAB result type: {type(result)}")

    assert np.allclose(result_list, expected, equal_nan=True), f"Expected {expected}, got {result_list}"
