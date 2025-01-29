import pytest
import numpy as np
import json

@pytest.fixture
def sample_stats():
    """Create a stats struct."""
    stats_entry = {
        "n": 1.0, "Cp": float("nan"), "Fmax": float("nan"), "p": float("nan"),
        "b0": float("nan"), "b1": float("nan"), "b2": float("nan"), "c2": float("nan"),
        "cib0": float("nan"), "cib1": float("nan"), "cic2": float("nan"),
        "mt": float("nan"), "ti": float("nan"), "tf": float("nan"),
        "ruStarVsT": float("nan"), "puStarVsT": float("nan"),
        "mT": float("nan"), "ciT": float("nan")
    }
    return stats_entry

@pytest.mark.parametrize(
    "field_name, expected",
    [
        ("n", [[1.0]]),
        ("Cp", [[np.nan]])
    ]
)
def test_fcReadFields_valid(test_engine, sample_stats, field_name, expected):
    """Test fcReadFields with a single-entry JSON."""
    sample_stats_json = json.dumps(sample_stats, indent = 4)
    result = test_engine.fcReadFields(sample_stats_json, field_name, 'jsondecode', 1)
    assert test_engine.equal(result, test_engine.convert(expected))

    result = test_engine.fcReadFields(sample_stats, field_name)
    assert test_engine.equal(result, test_engine.convert(expected))


@pytest.fixture
def multi_stats_json():
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
    return json.dumps(multi_stats, indent = 4)

@pytest.mark.parametrize(
    "field_name, expected",
    [
        ("n", [[[1.0, 1.0], [1.0, 1.0]], [[1.0, 1.0], [1.0, 1.0]]]),
        ("Cp", [[[np.nan, np.nan], [np.nan, np.nan]],
                [[np.nan, np.nan], [np.nan, np.nan]]]),
    ]
)
def test_fcReadFields_multi(test_engine, multi_stats_json, field_name, expected):
    """Test fcReadFields with a multi-entry JSON."""
    result = test_engine.fcReadFields(multi_stats_json, field_name, 'jsondecode', 1)
    assert test_engine.equal(result, test_engine.convert(expected))