'''
oneflux.partition.compu

For license information:
see LICENSE file or headers in oneflux.__init__.py

"Compu" text function calls from original code implemented as actual functions 

@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2017-01-31
'''
import os
import sys
import logging
import numpy

from datetime import datetime
from oneflux import ONEFluxError
from oneflux.partition.ecogeo import sunrs
from oneflux.partition.auxiliary import FLOAT_PREC

_log = logging.getLogger(__name__)


def compu_qcnee_filter(data):
    """
    Assigns zero to all entries in QCNEE

    :param data: data structure for partitioning
    :type data: numpy.ndarray
    """
    return numpy.zeros(data.size, dtype='f4')


def compu_sunrise(data, julday, lat):
    """
    Computes sunrise times

    :param data: data structure for partitioning
    :type data: numpy.ndarray
    """
    sunrise, _ = sunrs(doy=julday, lat=lat)
    return sunrise


def compu_sunset(data, julday, lat):
    """
    Computes sunset times

    :param data: data structure for partitioning
    :type data: numpy.ndarray
    """
    _, sunset = sunrs(doy=julday, lat=lat)
    return sunset


def compu_daylight(data, hr, sunrise, sunset):
    """
    Computes binary daylight flag: day (1) night (0)

    :param data: data structure for partitioning
    :type data: numpy.ndarray
    """
    return ((hr > sunrise) & (hr < sunset))


def compu_daylight_zero(data):
    """
    Computes binary daylight flag as all night (0)

    :param data: data structure for partitioning
    :type data: numpy.ndarray
    """
    return numpy.zeros(data.size, dtype=FLOAT_PREC)


def compu_nee_night(data, nee):
    """
    Assigns NEE to NEENight

    :param data: data structure for partitioning
    :type data: numpy.ndarray
    """
    return nee


if __name__ == '__main__':
    raise ONEFluxError('Not executable')
