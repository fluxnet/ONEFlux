# Contains tests for testing the fcr2Calc function
# which computes an r^2 value for two datasets

import pytest
import numpy as np
import pandas as pd
from tests.conftest import test_engine

from hypothesis import given, settings, HealthCheck
from hypothesis.strategies import floats, lists, composite
import os

@composite
def float_list(draw, exclude_non_constant=True):
  x0 = draw(floats(min_value=1.1,max_value=10000))
  xs = draw(lists(floats(allow_infinity=False, min_value=-1e9, max_value=1e9), min_size=1, max_size=4))
  ys = [x0] + xs
  maxval = max(ys)
  # If we want to exclude non-constant lists, we add a constant to the first element
  if exclude_non_constant:
    return [ys[0] + maxval] + ys[1:]
  else:
    return ys

@composite
# Generate two lists of the same length that are at least length 2 and
# contain at least one float that is non-zero
def same_len_float_lists(draw):
  x = draw(float_list())
  y0 = draw(floats(min_value=0.1,max_value=100000))
  fixed_len = lists(floats(allow_infinity=False, min_value=-1e9, max_value=1e9), min_size=len(x)-1, max_size=len(x)-1)
  return (x, [y0] + draw(fixed_len))

# Properties of R2 measure

## R2 measure should be invariant under scaling
@given(list_data=same_len_float_lists(),
      scalar=floats(min_value=0.1,max_value=1000))
@settings(deadline=1000)
def test_r2_scale_invariance(test_engine, list_data, scalar):
  data1, data2 = list_data
  conv = test_engine.convert
 
  # Calculate R2 for the original data 
  r2 = test_engine.fcr2Calc(conv(data1), conv(data2))

  # Scale it
  data1_scaled = [scalar*x for x in data1]
  data2_scaled = [scalar*x for x in data2]

  # Calculate R2 for the scaled data 
  r2_scale = test_engine.fcr2Calc(conv(data1_scaled), conv(data2_scaled))

  # Should be equal
  assert test_engine.equal(r2, r2_scale)

## R2 measure should be invariant under translation
@given(list_data=same_len_float_lists())
@settings(deadline=1000)
def test_r2_translation_invariance(test_engine, list_data):
  data1, data2 = list_data
  conv = test_engine.convert
 
  # Calculate R2 for the original data 
  r2 = test_engine.fcr2Calc(conv(data1), conv(data2))

  # Translate it
  data1_translated = [x + 1 for x in data1]
  data2_translated = [x + 1 for x in data2]

  # Calculate R2 for the translated data 
  r2_translated = test_engine.fcr2Calc(conv(data1_translated), conv(data2_translated))

  # Should be equal
  assert test_engine.equal(r2, r2_translated)

## R2 measure should be 1 when data sets are equal

# Note: we are excluding data sets that are constant
# which might be a problem, see:
# https://github.com/fluxnet/ONEFlux/issues/81

@given(data1=float_list(exclude_non_constant=True),)
def test_r2_measure_properties_more(test_engine, data1):
  conv = test_engine.convert
  # R2 measures should be 1 when the two datasets are the same
  r2_same = test_engine.fcr2Calc(conv(data1), conv(data1))
  assert (r2_same == 1)

# Some specific test fixtures for R2 measure
@pytest.mark.parametrize('data1, data2, expected', [
  ([1, 2, 3], [1, 2, 3], 1),
  ([1, 2, 3], [1, 2, 4], 2.5),
  ([1, 2, 3], [1, 2, 5], 5.0),
  ([1, 2, 3], [1, 2, 6], 8.5),
  ([0.0,-10.0,20.0,2.0], [0.0,-10.0,22.0,0.0], 1.170940170940171),
])
def test_r2_measure_properties(test_engine, data1, data2, expected):
  conv = test_engine.convert
  # R2 measures should be 1 when the two datasets are the same
  r2 = test_engine.fcr2Calc(conv(data1), conv(data2))
  assert test_engine.equal(r2, expected)