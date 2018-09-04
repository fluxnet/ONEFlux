'''
oneflux.partition.ecogeo

For license information:
see LICENSE file or headers in oneflux.__init__.py

Eco and Geo functions for partitioning

@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2017-01-31
'''
import sys
import logging
import numpy

from datetime import datetime, timedelta

from oneflux import ONEFluxError
from oneflux.partition.auxiliary import FLOAT_PREC, DOUBLE_PREC

_log = logging.getLogger(__name__)


TREF = 15.0 # is degC in code (should be K 273.15?)
T0 = -46.02  # is degC in code (should be K 227.13?)


def lloyd_taylor(ta, rref, e0, tref=TREF, t0=T0):
    """
    Respiration as related to temperature.
    Adapted from soil respiration relation to soil temperature in eqn 11 from
    J. Lloyd, J. A. Taylor. On the temperature dependence of soil respiration. Functional Ecology, 1994, vol. 8, n. 3, pp. 315-323.
    http://dx.doi.org/10.2307/2389824
    
    :param ta: degC, air temperature, obtained from data
    :type ta: float
    :param rref: umolC m-2 -s, base respiration at reference temperature (tref),
                 initial value mean nighttime NEE, accepted range > 0,
                 alternative: none, whole parameter set is not used
                 rd15 in original code
    :type rref: float
    :param e0: degC, temperature sensitivity, initial value 100.0,
               accepted range 50.0 - 400.0,
               alternative: previous window, if exists, else <50: 50, >400: 400
               E0 in original code
    :type e0: float
    :param tref: degC, reference temperature (usually: 10 or 15 degC)
    :type tref: float
    :param t0: degC, regression parameter (usually: -46.02 degC)
    :type t0: float
    :rtype: float
    """

    # respiration based on temperature
    return rref * numpy.exp(e0 * ((1 / (tref - t0)) - (1 / (ta - t0))))



def sunrs(doy, lat):
    """
    Calculates sunrise and sunset times based on day of the year
    (sometimes called 'julian' day) and latitude
    Uses true solar time method from
    E. Linacre, 1992. Climate Data and Resources: A Reference and Guide.
    
    :param doy: day of the year
    :type doy: int
    :param lat: Latitude of site
    :type lat: float
    """
    # always 80.0, in original code was:
    # dt_to_sec(str_to_dt('21-3-1997', date_fmt=2), base = '1-1-1997') / 86400 + 1
    march21_doy_diff = (datetime(1997, 3, 21) - datetime(1997, 1, 1)).days + 1

    pi = 3.1415926
    rad_per_day = 2.0 * pi / 365.0
    decl_amp_li = 23.45 * pi / 180.0
    hours_per_hs = 24 / (2.0 * pi)  # original comment: 24 hour is 2pi

    lat_rad = lat * pi / 180.0
    decl = decl_amp_li * numpy.sin(rad_per_day * (doy - march21_doy_diff))

    hs = numpy.arccos(-numpy.tan(lat_rad) * numpy.tan(decl))
    sunrise = 12 - hs * hours_per_hs
    sunset = 12 + hs * hours_per_hs

    return (sunrise, sunset)



def lloyd_taylor_dt(ta_f, parameter, tref=TREF, t0=T0):
    """
    Respiration as related to temperature.
    Adapted from soil respiration relation to soil temperature in eqn 11 from
    J. Lloyd, J. A. Taylor. On the temperature dependence of soil respiration. Functional Ecology, 1994, vol. 8, n. 3, pp. 315-323.
    http://dx.doi.org/10.2307/2389824
    
    :param ta: degC, air temperature, obtained from data
    :type ta: float
    :param rref: umolC m-2 -s, base respiration at reference temperature (tref),
                 initial value mean nighttime NEE, accepted range > 0,
                 alternative: none, whole parameter set is not used
                 rd15 in original code
    :type rref: float
    :param e0: degC, temperature sensitivity, initial value 100.0,
               accepted range 50.0 - 400.0,
               alternative: previous window, if exists, else <50: 50, >400: 400
               E0 in original code
    :type e0: float
    :param tref: degC, reference temperature (usually: 10 or 15 degC)
    :type tref: float
    :param t0: degC, regression parameter (usually: -46.02 degC)
    :type t0: float
    :rtype: float
    """
    rd15 = parameter[0]
    e0 = parameter[1]

    # respiration based on temperature
    return rd15 * numpy.exp(e0 * ((1 / (tref - t0)) - (1 / (ta_f - t0))))


def hlrc_lloyd(rg_f, ta_f, e0, parameter, tref=TREF, t0=T0):
    """
    Respiration as related to temperature.
    Adapted from soil respiration relation to soil temperature in eqn 11 from
    J. Lloyd, J. A. Taylor. On the temperature dependence of soil respiration. Functional Ecology, 1994, vol. 8, n. 3, pp. 315-323.
    http://dx.doi.org/10.2307/2389824
    
    :param ta: degC, air temperature, obtained from data
    :type ta: float
    :param rref: umolC m-2 -s, base respiration at reference temperature (tref),
                 initial value mean nighttime NEE, accepted range > 0,
                 alternative: none, whole parameter set is not used
                 rd15 in original code
    :type rref: float
    :param e0: degC, temperature sensitivity, initial value 100.0,
               accepted range 50.0 - 400.0,
               alternative: previous window, if exists, else <50: 50, >400: 400
               E0 in original code
    :type e0: float
    :param tref: degC, reference temperature (usually: 10 or 15 degC)
    :type tref: float
    :param t0: degC, regression parameter (usually: -46.02 degC)
    :type t0: float
    :rtype: float
    """
    alpha = parameter[0]
    beta = parameter[1]
    rd15 = parameter[2]

    # respiration based on temperature
    resp = rd15 * numpy.exp(e0 * ((1 / (tref - t0)) - (1 / (ta_f - t0))))
    fc = -1 * alpha * beta * rg_f / (alpha * rg_f + beta) + resp

    return fc


def hlrc_lloydvpd(rg_f, ta_f, e0, vpd_f, parameter, tref=TREF, t0=T0):
    """
    Respiration as related to temperature.
    Adapted from soil respiration relation to soil temperature in eqn 11 from
    J. Lloyd, J. A. Taylor. On the temperature dependence of soil respiration. Functional Ecology, 1994, vol. 8, n. 3, pp. 315-323.
    http://dx.doi.org/10.2307/2389824
    
    :param ta: degC, air temperature, obtained from data
    :type ta: float
    :param rref: umolC m-2 -s, base respiration at reference temperature (tref),
                 initial value mean nighttime NEE, accepted range > 0,
                 alternative: none, whole parameter set is not used
                 rd15 in original code
    :type rref: float
    :param e0: degC, temperature sensitivity, initial value 100.0,
               accepted range 50.0 - 400.0,
               alternative: previous window, if exists, else <50: 50, >400: 400
               E0 in original code
    :type e0: float
    :param tref: degC, reference temperature (usually: 10 or 15 degC)
    :type tref: float
    :param t0: degC, regression parameter (usually: -46.02 degC)
    :type t0: float
    :rtype: float
    """
    alpha = parameter[0]
    beta = parameter[1]
    k = parameter[2]
    rd15 = parameter[3]

    # respiration based on temperature
    resp = rd15 * numpy.exp(e0 * ((1 / (tref - t0)) - (1 / (ta_f - t0))))

    replicated_arr = numpy.empty(vpd_f.size)
    replicated_arr.fill(1.0)
    min_arr = numpy.minimum(numpy.exp(-1 * k * (vpd_f - 10.0)), replicated_arr)

    fc = -1 * alpha * beta * min_arr * rg_f / (alpha * rg_f + beta * min_arr) + resp

    return fc


def hlrc_lloyd_afix(rg_f, ta_f, e0, alpha, parameter, tref=TREF, t0=T0):
    """
    Respiration as related to temperature.
    Adapted from soil respiration relation to soil temperature in eqn 11 from
    J. Lloyd, J. A. Taylor. On the temperature dependence of soil respiration. Functional Ecology, 1994, vol. 8, n. 3, pp. 315-323.
    http://dx.doi.org/10.2307/2389824
    
    :param ta: degC, air temperature, obtained from data
    :type ta: float
    :param rref: umolC m-2 -s, base respiration at reference temperature (tref),
                 initial value mean nighttime NEE, accepted range > 0,
                 alternative: none, whole parameter set is not used
                 rd15 in original code
    :type rref: float
    :param e0: degC, temperature sensitivity, initial value 100.0,
               accepted range 50.0 - 400.0,
               alternative: previous window, if exists, else <50: 50, >400: 400
               E0 in original code
    :type e0: float
    :param tref: degC, reference temperature (usually: 10 or 15 degC)
    :type tref: float
    :param t0: degC, regression parameter (usually: -46.02 degC)
    :type t0: float
    :rtype: float
    """
    beta = parameter[0]
    rd15 = parameter[1]

    # respiration based on temperature
    resp = rd15 * numpy.exp(e0 * ((1 / (tref - t0)) - (1 / (ta_f - t0))))
    fc = -1 * alpha * beta * rg_f / (alpha * rg_f + beta) + resp

    return fc


def hlrc_lloydvpd_afix(rg_f, ta_f, e0, vpd_f, alpha, parameter, tref=TREF, t0=T0):
    """
    Respiration as related to temperature.
    Adapted from soil respiration relation to soil temperature in eqn 11 from
    J. Lloyd, J. A. Taylor. On the temperature dependence of soil respiration. Functional Ecology, 1994, vol. 8, n. 3, pp. 315-323.
    http://dx.doi.org/10.2307/2389824
    
    :param ta: degC, air temperature, obtained from data
    :type ta: float
    :param rref: umolC m-2 -s, base respiration at reference temperature (tref),
                 initial value mean nighttime NEE, accepted range > 0,
                 alternative: none, whole parameter set is not used
                 rd15 in original code
    :type rref: float
    :param e0: degC, temperature sensitivity, initial value 100.0,
               accepted range 50.0 - 400.0,
               alternative: previous window, if exists, else <50: 50, >400: 400
               E0 in original code
    :type e0: float
    :param tref: degC, reference temperature (usually: 10 or 15 degC)
    :type tref: float
    :param t0: degC, regression parameter (usually: -46.02 degC)
    :type t0: float
    :rtype: float
    """
    beta = parameter[0]
    k = parameter[1]
    rd15 = parameter[2]

    # respiration based on temperature
    resp = rd15 * numpy.exp(e0 * ((1 / (tref - t0)) - (1 / (ta_f - t0))))

    replicated_arr = numpy.empty(vpd_f.size)
    replicated_arr.fill(1.0)
    min_arr = numpy.minimum(numpy.exp(-1 * k * (vpd_f - 10.)), replicated_arr)

    fc = -1 * alpha * beta * min_arr * rg_f / (alpha * rg_f + beta * min_arr) + resp

    return fc


def lloydt_e0fix(ta_f, e0, parameter, tref=TREF, t0=T0):
    """
    Respiration as related to temperature.
    Adapted from soil respiration relation to soil temperature in eqn 11 from
    J. Lloyd, J. A. Taylor. On the temperature dependence of soil respiration. Functional Ecology, 1994, vol. 8, n. 3, pp. 315-323.
    http://dx.doi.org/10.2307/2389824
    
    :param ta: degC, air temperature, obtained from data
    :type ta: float
    :param rref: umolC m-2 -s, base respiration at reference temperature (tref),
                 initial value mean nighttime NEE, accepted range > 0,
                 alternative: none, whole parameter set is not used
                 rd15 in original code
    :type rref: float
    :param e0: degC, temperature sensitivity, initial value 100.0,
               accepted range 50.0 - 400.0,
               alternative: previous window, if exists, else <50: 50, >400: 400
               E0 in original code
    :type e0: float
    :param tref: degC, reference temperature (usually: 10 or 15 degC)
    :type tref: float
    :param t0: degC, regression parameter (usually: -46.02 degC)
    :type t0: float
    :rtype: float
    """

    rd15 = parameter
    if isinstance(parameter, list):
        rd15 = parameter[0]

    # respiration based on temperature
    return rd15 * numpy.exp(e0 * ((1 / (tref - t0)) - (1 / (ta_f - t0))))


def gpp_vpd(rg_f, vpd_f, parameter):
    """
    Respiration as related to temperature.
    Adapted from soil respiration relation to soil temperature in eqn 11 from
    J. Lloyd, J. A. Taylor. On the temperature dependence of soil respiration. Functional Ecology, 1994, vol. 8, n. 3, pp. 315-323.
    http://dx.doi.org/10.2307/2389824
    
    :param ta: degC, air temperature, obtained from data
    :type ta: float
    :param rref: umolC m-2 -s, base respiration at reference temperature (tref),
                 initial value mean nighttime NEE, accepted range > 0,
                 alternative: none, whole parameter set is not used
                 rd15 in original code
    :type rref: float
    :param e0: degC, temperature sensitivity, initial value 100.0,
               accepted range 50.0 - 400.0,
               alternative: previous window, if exists, else <50: 50, >400: 400
               E0 in original code
    :type e0: float
    :param tref: degC, reference temperature (usually: 10 or 15 degC)
    :type tref: float
    :param t0: degC, regression parameter (usually: -46.02 degC)
    :type t0: float
    :rtype: float
    """
    alpha = parameter[0]
    beta = parameter[1]
    k = parameter[2]

    gpp = None
    if beta == 0:
        gpp = numpy.zeros(len(rg_f), dtype=FLOAT_PREC)
    else:
        replicated_arr = numpy.empty(vpd_f.size)
        replicated_arr.fill(1.0)
        min_arr = numpy.minimum(numpy.exp(-1 * k * (vpd_f - 10.)), replicated_arr)
        gpp = alpha * beta * min_arr * rg_f / (alpha * rg_f + beta * min_arr)

    return gpp


if __name__ == '__main__':
    raise ONEFluxError('Not executable')
