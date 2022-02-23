'''
oneflux.pipeline.variable_codes

For license information:
see LICENSE file or headers in oneflux.__init__.py

Variable list / codes / map

@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2015-12-08
'''

import sys
import os
import logging

from oneflux import ONEFluxError

log = logging.getLogger(__name__)

PERC_LABEL = '_QC' # NEW FOR APRIL2016

TIMESTAMP_VARIABLE_LIST = [
'TIMESTAMP',
'TIMESTAMP_START',
'TIMESTAMP_END']


VARIABLE_LIST_FULL = [
'TIMESTAMP',
'TIMESTAMP_START',
'TIMESTAMP_END',

### MICROMETEOROLOGICAL
'TA_F_MDS',
'TA_F_MDS_QC',
'TA_F_MDS_NIGHT',
'TA_F_MDS_NIGHT_SD',
'TA_F_MDS_NIGHT_QC',
'TA_F_MDS_DAY',
'TA_F_MDS_DAY_SD',
'TA_F_MDS_DAY_QC',
'TA_ERA',
'TA_ERA_NIGHT',
'TA_ERA_NIGHT_SD',
'TA_ERA_DAY',
'TA_ERA_DAY_SD',
'TA_F',
'TA_F_QC',
'TA_F_NIGHT',
'TA_F_NIGHT_SD',
'TA_F_NIGHT_QC',
'TA_F_DAY',
'TA_F_DAY_SD',
'TA_F_DAY_QC',
'SW_IN_POT',
'SW_IN_F_MDS',
'SW_IN_F_MDS_QC',
'SW_IN_ERA',
'SW_IN_F',
'SW_IN_F_QC',
'LW_IN_F_MDS',
'LW_IN_F_MDS_QC',
'LW_IN_ERA',
'LW_IN_F',
'LW_IN_F_QC',
'LW_IN_JSB',
'LW_IN_JSB_QC',
'LW_IN_JSB_ERA',
'LW_IN_JSB_F',
'LW_IN_JSB_F_QC',
'VPD_F_MDS',
'VPD_F_MDS_QC',
'VPD_ERA',
'VPD_F',
'VPD_F_QC',
'PA',
'PA_ERA',
'PA_F',
'PA_F_QC',
'P',
'P_ERA',
'P_F',
'P_F_QC',
'WS',
'WS_ERA',
'WS_F',
'WS_F_QC',
'WD', # NEW FOR APRIL2016
'WD' + PERC_LABEL, # NEW FOR APRIL2016
'USTAR', # NEW FOR APRIL2016
'USTAR' + PERC_LABEL, # NEW FOR APRIL2016
'RH', # FIX FOR JULY2016
'RH' + PERC_LABEL, # FIX FOR JULY2016
'NETRAD', # NEW FOR APRIL2016
'NETRAD' + PERC_LABEL, # NEW FOR APRIL2016
'PPFD_IN', # NEW FOR APRIL2016
'PPFD_IN' + PERC_LABEL, # NEW FOR APRIL2016
'PPFD_DIF', # NEW FOR APRIL2016
'PPFD_DIF' + PERC_LABEL, # NEW FOR APRIL2016
'PPFD_OUT', # NEW FOR APRIL2016
'PPFD_OUT' + PERC_LABEL, # NEW FOR APRIL2016
'SW_DIF', # NEW FOR APRIL2016
'SW_DIF' + PERC_LABEL, # NEW FOR APRIL2016
'SW_OUT', # NEW FOR APRIL2016
'SW_OUT' + PERC_LABEL, # NEW FOR APRIL2016
'LW_OUT', # NEW FOR APRIL2016
'LW_OUT' + PERC_LABEL, # NEW FOR APRIL2016
'CO2_F_MDS',
'CO2_F_MDS_QC',
] + \
['TS_F_MDS_{n}'.format(n=i) for i in range(1, 20)] + \
['TS_F_MDS_{n}_QC'.format(n=i) for i in range(1, 20)] + \
['SWC_F_MDS_{n}'.format(n=i) for i in range(1, 20)] + \
['SWC_F_MDS_{n}_QC'.format(n=i) for i in range(1, 20)] + \
[
### ENERGY PROCESSING
'G_F_MDS', # NEW FOR APRIL2016
'G_F_MDS_QC', # NEW FOR APRIL2016
'LE_F_MDS',
'LE_F_MDS_QC',
'LE_CORR',
'LE_CORR_25',
'LE_CORR_75',
'LE_RANDUNC',
'LE_RANDUNC_METHOD',
'LE_RANDUNC_N',
'LE_CORR_JOINTUNC',
'H_F_MDS',
'H_F_MDS_QC',
'H_CORR',
'H_CORR_25',
'H_CORR_75',
'H_RANDUNC',
'H_RANDUNC_METHOD',
'H_RANDUNC_N',
'H_CORR_JOINTUNC',
'EBC_CF_N',
'EBC_CF_METHOD',

### NET ECOSYSTEM EXCHANGE
'NIGHT',
'NIGHT_D',
'DAY_D',
'NIGHT_RANDUNC_N',
'DAY_RANDUNC_N',
'NEE_CUT_REF',
'NEE_VUT_REF',
'NEE_CUT_REF_QC',
'NEE_VUT_REF_QC',
'NEE_CUT_REF_RANDUNC',
'NEE_VUT_REF_RANDUNC',
'NEE_CUT_REF_RANDUNC_METHOD',
'NEE_VUT_REF_RANDUNC_METHOD',
'NEE_CUT_REF_RANDUNC_N',
'NEE_VUT_REF_RANDUNC_N',
'NEE_CUT_REF_JOINTUNC',
'NEE_VUT_REF_JOINTUNC',
'NEE_CUT_USTAR50',
'NEE_VUT_USTAR50',
'NEE_CUT_USTAR50_QC',
'NEE_VUT_USTAR50_QC',
'NEE_CUT_USTAR50_RANDUNC',
'NEE_VUT_USTAR50_RANDUNC',
'NEE_CUT_USTAR50_RANDUNC_METHOD',
'NEE_VUT_USTAR50_RANDUNC_METHOD',
'NEE_CUT_USTAR50_RANDUNC_N',
'NEE_VUT_USTAR50_RANDUNC_N',
'NEE_CUT_USTAR50_JOINTUNC',
'NEE_VUT_USTAR50_JOINTUNC',
'NEE_CUT_MEAN',
'NEE_VUT_MEAN',
'NEE_CUT_MEAN_QC',
'NEE_VUT_MEAN_QC',
'NEE_CUT_SE',
'NEE_VUT_SE',
] + \
['NEE_CUT_{n}'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
['NEE_VUT_{n}'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
['NEE_CUT_{n}_QC'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
['NEE_VUT_{n}_QC'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[
'NEE_CUT_REF_NIGHT',
'NEE_VUT_REF_NIGHT',
'NEE_CUT_REF_NIGHT_SD',
'NEE_VUT_REF_NIGHT_SD',
'NEE_CUT_REF_NIGHT_QC',
'NEE_VUT_REF_NIGHT_QC',
'NEE_CUT_REF_NIGHT_RANDUNC',
'NEE_VUT_REF_NIGHT_RANDUNC',
'NEE_CUT_REF_NIGHT_JOINTUNC',
'NEE_VUT_REF_NIGHT_JOINTUNC',
'NEE_CUT_REF_DAY',
'NEE_VUT_REF_DAY',
'NEE_CUT_REF_DAY_SD',
'NEE_VUT_REF_DAY_SD',
'NEE_CUT_REF_DAY_QC',
'NEE_VUT_REF_DAY_QC',
'NEE_CUT_REF_DAY_RANDUNC',
'NEE_VUT_REF_DAY_RANDUNC',
'NEE_CUT_REF_DAY_JOINTUNC',
'NEE_VUT_REF_DAY_JOINTUNC',
'NEE_CUT_USTAR50_NIGHT',
'NEE_VUT_USTAR50_NIGHT',
'NEE_CUT_USTAR50_NIGHT_SD',
'NEE_VUT_USTAR50_NIGHT_SD',
'NEE_CUT_USTAR50_NIGHT_QC',
'NEE_VUT_USTAR50_NIGHT_QC',
'NEE_CUT_USTAR50_NIGHT_RANDUNC',
'NEE_VUT_USTAR50_NIGHT_RANDUNC',
'NEE_CUT_USTAR50_NIGHT_JOINTUNC',
'NEE_VUT_USTAR50_NIGHT_JOINTUNC',
'NEE_CUT_USTAR50_DAY',
'NEE_VUT_USTAR50_DAY',
'NEE_CUT_USTAR50_DAY_SD',
'NEE_VUT_USTAR50_DAY_SD',
'NEE_CUT_USTAR50_DAY_QC',
'NEE_VUT_USTAR50_DAY_QC',
'NEE_CUT_USTAR50_DAY_RANDUNC',
'NEE_VUT_USTAR50_DAY_RANDUNC',
'NEE_CUT_USTAR50_DAY_JOINTUNC',
'NEE_VUT_USTAR50_DAY_JOINTUNC',
] + \
['NEE_CUT_{n}_NIGHT'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
['NEE_VUT_{n}_NIGHT'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
['NEE_CUT_{n}_NIGHT_QC'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
['NEE_VUT_{n}_NIGHT_QC'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
['NEE_CUT_{n}_DAY'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
['NEE_VUT_{n}_DAY'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
['NEE_CUT_{n}_DAY_QC'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
['NEE_VUT_{n}_DAY_QC'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[

### PARTITIONING NIGHTTIME
'RECO_NT_VUT_REF',
'RECO_NT_VUT_USTAR50',
'RECO_NT_VUT_MEAN',
'RECO_NT_VUT_SE',
] + \
['RECO_NT_VUT_{n}'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[
'RECO_NT_CUT_REF',
'RECO_NT_CUT_USTAR50',
'RECO_NT_CUT_MEAN',
'RECO_NT_CUT_SE',
] + \
['RECO_NT_CUT_{n}'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[
'GPP_NT_VUT_REF',
'GPP_NT_VUT_USTAR50',
'GPP_NT_VUT_MEAN',
'GPP_NT_VUT_SE',
] + \
['GPP_NT_VUT_{n}'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[
'GPP_NT_CUT_REF',
'GPP_NT_CUT_USTAR50',
'GPP_NT_CUT_MEAN',
'GPP_NT_CUT_SE',
] + \
['GPP_NT_CUT_{n}'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[

### PARTITIONING DAYTIME
'RECO_DT_VUT_REF',
'RECO_DT_VUT_USTAR50',
'RECO_DT_VUT_MEAN',
'RECO_DT_VUT_SE',
] + \
['RECO_DT_VUT_{n}'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[
'RECO_DT_CUT_REF',
'RECO_DT_CUT_USTAR50',
'RECO_DT_CUT_MEAN',
'RECO_DT_CUT_SE',
] + \
['RECO_DT_CUT_{n}'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[
'GPP_DT_VUT_REF',
'GPP_DT_VUT_USTAR50',
'GPP_DT_VUT_MEAN',
'GPP_DT_VUT_SE',
] + \
['GPP_DT_VUT_{n}'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[
'GPP_DT_CUT_REF',
'GPP_DT_CUT_USTAR50',
'GPP_DT_CUT_MEAN',
'GPP_DT_CUT_SE',
] + \
['GPP_DT_CUT_{n}'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[

### PARTITIONING SUNDOWN
'RECO_SR',
'RECO_SR_N'
]

for i, e in enumerate(VARIABLE_LIST_FULL):
    if VARIABLE_LIST_FULL.count(e) != 1:
        raise ONEFluxError("Duplicated variable VARIABLE_LIST_FULL[{i}]: {v}".format(i=i, v=e))

VARIABLE_LIST_SUB = [
### TIMEKEEPING
'TIMESTAMP',
'TIMESTAMP_START',
'TIMESTAMP_END',

### MICROMETEOROLOGICAL
'TA_F',
'TA_F_QC',
'SW_IN_POT',
'SW_IN_F',
'SW_IN_F_QC',
'LW_IN_F',
'LW_IN_F_QC',
'VPD_F',
'VPD_F_QC',
'PA_F',
'PA_F_QC',
'P_F',
'P_F_QC',
'WS_F',
'WS_F_QC',
'WD', # NEW FOR APRIL2016
'WD' + PERC_LABEL, # NEW FOR APRIL2016
'USTAR', # NEW FOR APRIL2016
'USTAR' + PERC_LABEL, # NEW FOR APRIL2016
'RH', # FIX FOR JULY2016
'RH' + PERC_LABEL, # FIX FOR JULY2016
'NETRAD', # NEW FOR APRIL2016
'NETRAD' + PERC_LABEL, # NEW FOR APRIL2016
'PPFD_IN', # NEW FOR APRIL2016
'PPFD_IN' + PERC_LABEL, # NEW FOR APRIL2016
'PPFD_DIF', # NEW FOR APRIL2016
'PPFD_DIF' + PERC_LABEL, # NEW FOR APRIL2016
'PPFD_OUT', # NEW FOR APRIL2016
'PPFD_OUT' + PERC_LABEL, # NEW FOR APRIL2016
'SW_DIF', # NEW FOR APRIL2016
'SW_DIF' + PERC_LABEL, # NEW FOR APRIL2016
'SW_OUT', # NEW FOR APRIL2016
'SW_OUT' + PERC_LABEL, # NEW FOR APRIL2016
'LW_OUT', # NEW FOR APRIL2016
'LW_OUT' + PERC_LABEL, # NEW FOR APRIL2016
'CO2_F_MDS',
'CO2_F_MDS_QC',
] + \
['TS_F_MDS_{n}'.format(n=i) for i in range(1, 20)] + \
['TS_F_MDS_{n}_QC'.format(n=i) for i in range(1, 20)] + \
['SWC_F_MDS_{n}'.format(n=i) for i in range(1, 20)] + \
['SWC_F_MDS_{n}_QC'.format(n=i) for i in range(1, 20)] + \
[

### ENERGY PROCESSING
'G_F_MDS', # NEW FOR APRIL2016
'G_F_MDS_QC', # NEW FOR APRIL2016
'LE_F_MDS',
'LE_F_MDS_QC',
'LE_CORR',
'LE_CORR_25',
'LE_CORR_75',
'LE_RANDUNC',
'H_F_MDS',
'H_F_MDS_QC',
'H_CORR',
'H_CORR_25',
'H_CORR_75',
'H_RANDUNC',

### NET ECOSYSTEM EXCHANGE
'NIGHT',
'NEE_VUT_REF',
'NEE_VUT_REF_QC',
'NEE_VUT_REF_RANDUNC',
] + \
['NEE_VUT_{n}'.format(n=i) for i in ['25', '50', '75']] + \
['NEE_VUT_{n}_QC'.format(n=i) for i in ['25', '50', '75']] + \
[

### PARTITIONING
'RECO_NT_VUT_REF',
] + \
['RECO_NT_VUT_{n}'.format(n=i) for i in ['25', '50', '75']] + \
[
'GPP_NT_VUT_REF',
] + \
['GPP_NT_VUT_{n}'.format(n=i) for i in ['25', '50', '75']] + \
[
'RECO_DT_VUT_REF',
] + \
['RECO_DT_VUT_{n}'.format(n=i) for i in ['25', '50', '75']] + \
[
'GPP_DT_VUT_REF',
] + \
['GPP_DT_VUT_{n}'.format(n=i) for i in ['25', '50', '75']] + \
[
'RECO_SR',
'RECO_SR_N',
]

for i, e in enumerate(VARIABLE_LIST_SUB):
    if VARIABLE_LIST_SUB.count(e) != 1:
        raise ONEFluxError("Duplicated variable VARIABLE_LIST_FULL[{i}]: {v}".format(i=i, v=e))

VARIABLE_LIST_FULL_MAP = [
### TIMEKEEPING
['TIMESTAMP', ['TIMESTAMP', ]],
['TIMESTAMP_START', ['TIMESTAMP_START', ]],
['TIMESTAMP_END', ['TIMESTAMP_END', ]],

### MICROMETEOROLOGICAL
['TA_F_MDS', ['TA_f', 'Ta_f']],
['TA_F_MDS_QC', ['TA_fqc', 'Ta_fqc']],
['TA_F_MDS_NIGHT', ['TA_f_night', 'Ta_f_night']],
['TA_F_MDS_NIGHT_SD', ['TA_f_night_std', 'Ta_f_night_std']],
['TA_F_MDS_NIGHT_QC', ['TA_f_night_qc', 'Ta_f_night_qc']],
['TA_F_MDS_DAY', ['TA_f_day', 'Ta_f_day']],
['TA_F_MDS_DAY_SD', ['TA_f_day_std', 'Ta_f_day_std']],
['TA_F_MDS_DAY_QC', ['TA_f_day_qc', 'Ta_f_day_qc']],
['TA_ERA', ['TA_ERA', 'Ta_ERA']],
['TA_ERA_NIGHT', ['TA_ERA_night', 'Ta_ERA_night']],
['TA_ERA_NIGHT_SD', ['TA_ERA_night_std', 'Ta_ERA_night_std']],
['TA_ERA_DAY', ['TA_ERA_day', 'Ta_ERA_day']],
['TA_ERA_DAY_SD', ['TA_ERA_day_std', 'Ta_ERA_day_std']],
['TA_F', ['TA_m', 'Ta_m']],
['TA_F_QC', ['TA_mqc', 'Ta_mqc']],
['TA_F_NIGHT', ['TA_m_night', 'Ta_m_night']],
['TA_F_NIGHT_SD', ['TA_m_night_std', 'Ta_m_night_std']],
['TA_F_NIGHT_QC', ['TA_m_night_qc', 'Ta_m_night_qc']],
['TA_F_DAY', ['TA_m_day', 'Ta_m_day']],
['TA_F_DAY_SD', ['TA_m_day_std', 'Ta_m_day_std']],
['TA_F_DAY_QC', ['TA_m_day_qc', 'Ta_m_day_qc']],
['SW_IN_POT', ['SW_IN_pot', 'SWin_pot', 'RPOT']],
['SW_IN_F_MDS', ['SW_IN_f', 'SWin_f']],
['SW_IN_F_MDS_QC', ['SW_IN_fqc', 'SWin_fqc']],
['SW_IN_ERA', ['SW_IN_ERA', 'SWin_ERA']],
['SW_IN_F', ['SW_IN_m', 'SWin_m']],
['SW_IN_F_QC', ['SW_IN_mqc', 'SWin_mqc']],
['LW_IN_F_MDS', ['LW_IN_f', 'LWin_f']],
['LW_IN_F_MDS_QC', ['LW_IN_fqc', 'LWin_fqc']],
['LW_IN_ERA', ['LW_IN_ERA', 'LWin_ERA']],
['LW_IN_F', ['LW_IN_m', 'LWin_m']],
['LW_IN_F_QC', ['LW_IN_mqc', 'LWin_mqc']],
['LW_IN_JSB', ['LW_IN_calc', 'LWin_calc']],
['LW_IN_JSB_QC', ['LW_IN_calc_qc', 'LWin_calc_qc']],
['LW_IN_JSB_ERA', ['LW_IN_calc_ERA', 'LWin_calc_ERA']],
['LW_IN_JSB_F', ['LW_IN_calc_m', 'LWin_calc_m']],
['LW_IN_JSB_F_QC', ['LW_IN_calc_mqc', 'LWin_calc_mqc']],
['VPD_F_MDS', ['VPD_f', ]],
['VPD_F_MDS_QC', ['VPD_fqc', ]],
['VPD_ERA', ['VPD_ERA', ]],
['VPD_F', ['VPD_m', ]],
['VPD_F_QC', ['VPD_mqc', ]],
['PA', ['PA', 'Pa']],
['PA_ERA', ['PA_ERA', 'Pa_ERA']],
['PA_F', ['PA_m', 'Pa_m']],
['PA_F_QC', ['PA_mqc', 'Pa_mqc']],
['P', ['P', ]],
['P_ERA', ['P_ERA', ]],
['P_F', ['P_m', ]],
['P_F_QC', ['P_mqc', ]],
['WS', ['WS', ]],
['WS_ERA', ['WS_ERA', ]],
['WS_F', ['WS_m', ]],
['WS_F_QC', ['WS_mqc', ]],
['RH', ['RH', 'Rh' ]], # FIX FOR JULY2016
['RH' + PERC_LABEL, ['RH' + PERC_LABEL, ]], # FIX FOR JULY2016
['WD', ['WD', ]], # NEW FOR APRIL2016
['WD' + PERC_LABEL, ['WD' + PERC_LABEL, ]], # NEW FOR APRIL2016
['USTAR', ['USTAR', ]], # NEW FOR APRIL2016
['USTAR' + PERC_LABEL, ['USTAR' + PERC_LABEL, ]], # NEW FOR APRIL2016
['NETRAD', ['NETRAD', ]], # NEW FOR APRIL2016
['NETRAD' + PERC_LABEL, ['NETRAD' + PERC_LABEL, ]], # NEW FOR APRIL2016
['PPFD_IN', ['PPFD_IN', ]], # NEW FOR APRIL2016
['PPFD_IN' + PERC_LABEL, ['PPFD_IN' + PERC_LABEL, ]], # NEW FOR APRIL2016
['PPFD_DIF', ['PPFD_DIF', ]], # NEW FOR APRIL2016
['PPFD_DIF' + PERC_LABEL, ['PPFD_DIF' + PERC_LABEL, ]], # NEW FOR APRIL2016
['PPFD_OUT', ['PPFD_OUT', ]], # NEW FOR APRIL2016
['PPFD_OUT' + PERC_LABEL, ['PPFD_OUT' + PERC_LABEL, ]], # NEW FOR APRIL2016
['SW_DIF', ['SW_DIF', ]], # NEW FOR APRIL2016
['SW_DIF' + PERC_LABEL, ['SW_DIF' + PERC_LABEL, ]], # NEW FOR APRIL2016
['SW_OUT', ['SW_OUT', ]], # NEW FOR APRIL2016
['SW_OUT' + PERC_LABEL, ['SW_OUT' + PERC_LABEL, ]], # NEW FOR APRIL2016
['LW_OUT', ['LW_OUT', ]], # NEW FOR APRIL2016
['LW_OUT' + PERC_LABEL, ['LW_OUT' + PERC_LABEL, ]], # NEW FOR APRIL2016
['CO2_F_MDS', ['CO2_f', ]],
['CO2_F_MDS_QC', ['CO2_fqc', ]],
] + \
[['TS_F_MDS_{n}'.format(n=i), ['TS_{n}_f'.format(n=i), 'Ts_{n}_f'.format(n=i), ]] for i in range(20)] + \
[['TS_F_MDS_{n}_QC'.format(n=i), ['TS_{n}_fqc'.format(n=i), 'Ts_{n}_fqc'.format(n=i), ]] for i in range(20)] + \
[['SWC_F_MDS_{n}'.format(n=i), ['SWC_{n}_f'.format(n=i), ]] for i in range(20)] + \
[['SWC_F_MDS_{n}_QC'.format(n=i), ['SWC_{n}_fqc'.format(n=i), ]] for i in range(20)] + \
[

### ENERGY PROCESSING
['G_F_MDS', ['G_f', ]], # NEW FOR APRIL2016
['G_F_MDS_QC', ['G_qc', ]], # NEW FOR APRIL2016
['LE_F_MDS', ['LE', ]],
['LE_F_MDS_QC', ['LE_qc', ]],
['LE_CORR', ['LEcorr', ]],
['LE_CORR_25', ['LEcorr25', ]],
['LE_CORR_75', ['LEcorr75', ]],
['LE_RANDUNC', ['LE_randUnc', ]],
['LE_RANDUNC_METHOD', ['LE_randUnc_method', ]],
['LE_RANDUNC_N', ['LE_randUnc_n', ]],
['LE_CORR_JOINTUNC', ['LEcorr_joinUnc', ]],
['H_F_MDS', ['H', ]],
['H_F_MDS_QC', ['H_qc', ]],
['H_CORR', ['Hcorr', ]],
['H_CORR_25', ['Hcorr25', ]],
['H_CORR_75', ['Hcorr75', ]],
['H_RANDUNC', ['H_randUnc', ]],
['H_RANDUNC_METHOD', ['H_randUnc_method', ]],
['H_RANDUNC_N', ['H_randUnc_n', ]],
['H_CORR_JOINTUNC', ['Hcorr_joinUnc', ]],
['EBC_CF_N', ['EBCcf_n', ]],
['EBC_CF_METHOD', ['EBCcf_method', ]],

### NET ECOSYSTEM EXCHANGE
['NIGHT', ['night', ]],
['NIGHT_D', ['night_d', ]],
['DAY_D', ['day_d', ]],
['NIGHT_RANDUNC_N', ['night_randUnc_n', ]],
['DAY_RANDUNC_N', ['day_randUnc_n', ]],
['NEE_CUT_REF', ['NEE_ref_c', ]],
['NEE_VUT_REF', ['NEE_ref_y', ]],
['NEE_CUT_REF_QC', ['NEE_ref_qc_c', ]],
['NEE_VUT_REF_QC', ['NEE_ref_qc_y', ]],
['NEE_CUT_REF_RANDUNC', ['NEE_ref_randUnc_c', ]],
['NEE_VUT_REF_RANDUNC', ['NEE_ref_randUnc_y', ]],
['NEE_CUT_REF_RANDUNC_METHOD', ['NEE_ref_randUnc_method_c', ]],
['NEE_VUT_REF_RANDUNC_METHOD', ['NEE_ref_randUnc_method_y', ]],
['NEE_CUT_REF_RANDUNC_N', ['NEE_ref_randUnc_n_c', ]],
['NEE_VUT_REF_RANDUNC_N', ['NEE_ref_randUnc_n_y', ]],
['NEE_CUT_REF_JOINTUNC', ['NEE_ref_joinUnc_c', ]],
['NEE_VUT_REF_JOINTUNC', ['NEE_ref_joinUnc_y', ]],
['NEE_CUT_USTAR50', ['NEE_ust50_c', ]],
['NEE_VUT_USTAR50', ['NEE_ust50_y', ]],
['NEE_CUT_USTAR50_QC', ['NEE_ust50_qc_c', ]],
['NEE_VUT_USTAR50_QC', ['NEE_ust50_qc_y', ]],
['NEE_CUT_USTAR50_RANDUNC', ['NEE_ust50_randUnc_c', ]],
['NEE_VUT_USTAR50_RANDUNC', ['NEE_ust50_randUnc_y', ]],
['NEE_CUT_USTAR50_RANDUNC_METHOD', ['NEE_ust50_randUnc_method_c', ]],
['NEE_VUT_USTAR50_RANDUNC_METHOD', ['NEE_ust50_randUnc_method_y', ]],
['NEE_CUT_USTAR50_RANDUNC_N', ['NEE_ust50_randUnc_n_c', ]],
['NEE_VUT_USTAR50_RANDUNC_N', ['NEE_ust50_randUnc_n_y', ]],
['NEE_CUT_USTAR50_JOINTUNC', ['NEE_ust50_joinUnc_c', ]],
['NEE_VUT_USTAR50_JOINTUNC', ['NEE_ust50_joinUnc_y', ]],
['NEE_CUT_MEAN', ['NEE_mean_c', ]],
['NEE_VUT_MEAN', ['NEE_mean_y', ]],
['NEE_CUT_MEAN_QC', ['NEE_mean_qc_c', ]],
['NEE_VUT_MEAN_QC', ['NEE_mean_qc_y', ]],
['NEE_CUT_SE', ['NEE_SE_c', ]],
['NEE_VUT_SE', ['NEE_SE_y', ]],
] + \
[['NEE_CUT_{n}'.format(n=i), ['NEE_{n}_c'.format(n=i), ]] for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[['NEE_VUT_{n}'.format(n=i), ['NEE_{n}_y'.format(n=i), ]] for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[['NEE_CUT_{n}_QC'.format(n=i), ['NEE_{n}_qc_c'.format(n=i), ]] for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[['NEE_VUT_{n}_QC'.format(n=i), ['NEE_{n}_qc_y'.format(n=i), ]] for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[
['NEE_CUT_REF_NIGHT', ['NEE_ref_night_c', ]],
['NEE_VUT_REF_NIGHT', ['NEE_ref_night_y', ]],
['NEE_CUT_REF_NIGHT_SD', ['NEE_ref_night_std_c', ]],
['NEE_VUT_REF_NIGHT_SD', ['NEE_ref_night_std_y', ]],
['NEE_CUT_REF_NIGHT_QC', ['NEE_ref_night_qc_c', ]],
['NEE_VUT_REF_NIGHT_QC', ['NEE_ref_night_qc_y', ]],
['NEE_CUT_REF_NIGHT_RANDUNC', ['NEE_ref_night_randUnc_c', ]],
['NEE_VUT_REF_NIGHT_RANDUNC', ['NEE_ref_night_randUnc_y', ]],
['NEE_CUT_REF_NIGHT_JOINTUNC', ['NEE_ref_night_joinUnc_c', ]],
['NEE_VUT_REF_NIGHT_JOINTUNC', ['NEE_ref_night_joinUnc_y', ]],
['NEE_CUT_REF_DAY', ['NEE_ref_day_c', ]],
['NEE_VUT_REF_DAY', ['NEE_ref_day_y', ]],
['NEE_CUT_REF_DAY_SD', ['NEE_ref_day_std_c', ]],
['NEE_VUT_REF_DAY_SD', ['NEE_ref_day_std_y', ]],
['NEE_CUT_REF_DAY_QC', ['NEE_ref_day_qc_c', ]],
['NEE_VUT_REF_DAY_QC', ['NEE_ref_day_qc_y', ]],
['NEE_CUT_REF_DAY_RANDUNC', ['NEE_ref_day_randUnc_c', ]],
['NEE_VUT_REF_DAY_RANDUNC', ['NEE_ref_day_randUnc_y', ]],
['NEE_CUT_REF_DAY_JOINTUNC', ['NEE_ref_day_joinUnc_c', ]],
['NEE_VUT_REF_DAY_JOINTUNC', ['NEE_ref_day_joinUnc_y', ]],
['NEE_CUT_USTAR50_NIGHT', ['NEE_ust50_night_c', ]],
['NEE_VUT_USTAR50_NIGHT', ['NEE_ust50_night_y', ]],
['NEE_CUT_USTAR50_NIGHT_SD', ['NEE_ust50_night_std_c', ]],
['NEE_VUT_USTAR50_NIGHT_SD', ['NEE_ust50_night_std_y', ]],
['NEE_CUT_USTAR50_NIGHT_QC', ['NEE_ust50_night_qc_c', ]],
['NEE_VUT_USTAR50_NIGHT_QC', ['NEE_ust50_night_qc_y', ]],
['NEE_CUT_USTAR50_NIGHT_RANDUNC', ['NEE_ust50_night_randUnc_c', ]],
['NEE_VUT_USTAR50_NIGHT_RANDUNC', ['NEE_ust50_night_randUnc_y', ]],
['NEE_CUT_USTAR50_NIGHT_JOINTUNC', ['NEE_ust50_night_joinUnc_c', ]],
['NEE_VUT_USTAR50_NIGHT_JOINTUNC', ['NEE_ust50_night_joinUnc_y', ]],
['NEE_CUT_USTAR50_DAY', ['NEE_ust50_day_c', ]],
['NEE_VUT_USTAR50_DAY', ['NEE_ust50_day_y', ]],
['NEE_CUT_USTAR50_DAY_SD', ['NEE_ust50_day_std_c', ]],
['NEE_VUT_USTAR50_DAY_SD', ['NEE_ust50_day_std_y', ]],
['NEE_CUT_USTAR50_DAY_QC', ['NEE_ust50_day_qc_c', ]],
['NEE_VUT_USTAR50_DAY_QC', ['NEE_ust50_day_qc_y', ]],
['NEE_CUT_USTAR50_DAY_RANDUNC', ['NEE_ust50_day_randUnc_c', ]],
['NEE_VUT_USTAR50_DAY_RANDUNC', ['NEE_ust50_day_randUnc_y', ]],
['NEE_CUT_USTAR50_DAY_JOINTUNC', ['NEE_ust50_day_joinUnc_c', ]],
['NEE_VUT_USTAR50_DAY_JOINTUNC', ['NEE_ust50_day_joinUnc_y', ]],
] + \
[['NEE_CUT_{n}_NIGHT'.format(n=i), ['NEE_night_{n}_c'.format(n=i), ]] for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[['NEE_VUT_{n}_NIGHT'.format(n=i), ['NEE_night_{n}_y'.format(n=i), ]] for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[['NEE_CUT_{n}_NIGHT_QC'.format(n=i), ['NEE_night_{n}_qc_c'.format(n=i), ]] for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[['NEE_VUT_{n}_NIGHT_QC'.format(n=i), ['NEE_night_{n}_qc_y'.format(n=i), ]] for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[['NEE_CUT_{n}_DAY'.format(n=i), ['NEE_day_{n}_c'.format(n=i), ]] for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[['NEE_VUT_{n}_DAY'.format(n=i), ['NEE_day_{n}_y'.format(n=i), ]] for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[['NEE_CUT_{n}_DAY_QC'.format(n=i), ['NEE_day_{n}_qc_c'.format(n=i), ]] for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[['NEE_VUT_{n}_DAY_QC'.format(n=i), ['NEE_day_{n}_qc_y'.format(n=i), ]] for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[

### PARTITIONING NIGHTTIME
['RECO_NT_VUT_REF', ['NT_RECO_ref_y', ]],
['RECO_NT_VUT_USTAR50', ['NT_RECO_ust50_y', ]],
['RECO_NT_VUT_MEAN', ['NT_RECO_mean_y', ]],
['RECO_NT_VUT_SE', ['NT_RECO_SE_y', ]],
] + \
[['RECO_NT_VUT_{n}'.format(n=i), ['NT_RECO_{n}_y'.format(n=i)]] for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[
['RECO_NT_CUT_REF', ['NT_RECO_ref_c', ]],
['RECO_NT_CUT_USTAR50', ['NT_RECO_ust50_c', ]],
['RECO_NT_CUT_MEAN', ['NT_RECO_mean_c', ]],
['RECO_NT_CUT_SE', ['NT_RECO_SE_c', ]],
] + \
[['RECO_NT_CUT_{n}'.format(n=i), ['NT_RECO_{n}_c'.format(n=i)]] for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[
['GPP_NT_VUT_REF', ['NT_GPP_ref_y', ]],
['GPP_NT_VUT_USTAR50', ['NT_GPP_ust50_y', ]],
['GPP_NT_VUT_MEAN', ['NT_GPP_mean_y', ]],
['GPP_NT_VUT_SE', ['NT_GPP_SE_y', ]],
] + \
[['GPP_NT_VUT_{n}'.format(n=i), ['NT_GPP_{n}_y'.format(n=i)]] for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[
['GPP_NT_CUT_REF', ['NT_GPP_ref_c', ]],
['GPP_NT_CUT_USTAR50', ['NT_GPP_ust50_c', ]],
['GPP_NT_CUT_MEAN', ['NT_GPP_mean_c', ]],
['GPP_NT_CUT_SE', ['NT_GPP_SE_c', ]],
] + \
[['GPP_NT_CUT_{n}'.format(n=i), ['NT_GPP_{n}_c'.format(n=i)]] for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[

### PARTITIONING DAYTIME
['RECO_DT_VUT_REF', ['DT_RECO_ref_y', ]],
['RECO_DT_VUT_USTAR50', ['DT_RECO_ust50_y', ]],
['RECO_DT_VUT_MEAN', ['DT_RECO_mean_y', ]],
['RECO_DT_VUT_SE', ['DT_RECO_SE_y', ]],
] + \
[['RECO_DT_VUT_{n}'.format(n=i), ['DT_RECO_{n}_y'.format(n=i), ]] for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[
['RECO_DT_CUT_REF', ['DT_RECO_ref_c', ]],
['RECO_DT_CUT_USTAR50', ['DT_RECO_ust50_c', ]],
['RECO_DT_CUT_MEAN', ['DT_RECO_mean_c', ]],
['RECO_DT_CUT_SE', ['DT_RECO_SE_c', ]],
] + \
[['RECO_DT_CUT_{n}'.format(n=i), ['DT_RECO_{n}_c'.format(n=i), ]] for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[
['GPP_DT_VUT_REF', ['DT_GPP_ref_y', ]],
['GPP_DT_VUT_USTAR50', ['DT_GPP_ust50_y', ]],
['GPP_DT_VUT_MEAN', ['DT_GPP_mean_y', ]],
['GPP_DT_VUT_SE', ['DT_GPP_SE_y', ]],
] + \
[['GPP_DT_VUT_{n}'.format(n=i), ['DT_GPP_{n}_y'.format(n=i), ]] for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[
['GPP_DT_CUT_REF', ['DT_GPP_ref_c', ]],
['GPP_DT_CUT_USTAR50', ['DT_GPP_ust50_c', ]],
['GPP_DT_CUT_MEAN', ['DT_GPP_mean_c', ]],
['GPP_DT_CUT_SE', ['DT_GPP_SE_c', ]],
] + \
[['GPP_DT_CUT_{n}'.format(n=i), ['DT_GPP_{n}_c'.format(n=i), ]] for i in ['05', '16', '25', '50', '75', '84', '95']] + \
[

### PARTITIONING SUNDOWN
['RECO_SR', ['SR_RECO', ]],
['RECO_SR_N', ['SR_RECO_n', 'SR_RECO_N']],
]

FULL_DIRECT_D = {i[0]:i[1] for i in VARIABLE_LIST_FULL_MAP}

FULL_D = {}
for pair in VARIABLE_LIST_FULL_MAP:
    for old_e in pair[1]:
        if old_e in FULL_D:
            raise ONEFluxError("Duplicate old entry: '{e}'".format(e=old_e))
        else:
            FULL_D[old_e] = pair[0]

VARIABLE_LIST_SUB_MAP = [[i, FULL_DIRECT_D[i]] for i in VARIABLE_LIST_SUB]

SUB_D = {}
for pair in VARIABLE_LIST_SUB_MAP:
    for old_e in pair[1]:
        if old_e in SUB_D:
            raise ONEFluxError("Duplicate old entry: '{e}'".format(e=old_e))
        else:
            SUB_D[old_e] = pair[0]

QC_VARIABLE_LIST_FULL_MAP = [
['TIMESTAMP_START', ['TIMESTAMP_START', ]],
['TIMESTAMP_END', ['TIMESTAMP_END', 'ISOdate', 'Isodate', 'Timestamp', 'TIMESTAMP']],
['SW_IN_POT', ['SW_IN_POT', 'RPOT', 'Rpot']],
['NEE', ['NEE']],
['H', ['H']],
['LE', ['LE']],
['G', ['G', 'G1']],
['P', ['P', 'PREC', 'Prec', 'Precip']],
['NETRAD', ['NETRAD', 'NetRad', 'netrad']],
['CO2', ['CO2']],
['H2O', ['H2O']],
['FC', ['FC', 'Fc']],
['SW_IN', ['SW_IN', 'SWin', 'SW_in', 'Swin']],
['LW_IN', ['LW_IN', 'LWin', 'LW_in', 'Lwin']],
['SW_OUT', ['SW_OUT', 'SWout', 'SW_out', 'Swout']],
['LW_OUT', ['LW_OUT', 'LWout', 'LW_out', 'Lwout']],
['VPD', ['VPD']],
['TA', ['TA', 'Ta']],
['PA', ['PA', 'Pa', 'PRESS']],
['RH', ['RH', 'Rh']],
['USTAR', ['USTAR', 'ustar', 'Ustar', 'UStar']],
['WD', ['WD', 'Wd']],
['WS', ['WS', 'Ws']],
] + \
[['TS_{n}'.format(n=i), ['TS_{n}'.format(n=i), 'Ts_{n}'.format(n=i), ]] for i in range(20)] + \
[['SWC_{n}'.format(n=i), ['SWC_{n}'.format(n=i), ]] for i in range(20)] + \
[
['ZL', ['ZL']],
['FC_SSITC_TEST', ['FC_SSITC_TEST', 'QcFc']],
['H_SSITC_TEST', ['H_SSITC_TEST', 'QcH']],
['LE_SSITC_TEST', ['LE_SSITC_TEST', 'QcLE']],
['TR', ['TR', 'Tr']],
['SB', ['SB', 'Sb']],
['SC', ['SC', 'Sc']],
['SLE', ['SLE', 'SW', 'Sw']],
['SH', ['SH', 'SA', 'Sa']],
['SW_DIF', ['SW_DIF', ]],
['PPFD_IN', ['PPFD_IN', 'PAR', 'PARin', 'PAR_in', 'PPFDin', 'PPFD_in', 'PPFD']],
['PPFD_OUT', ['PPFD_OUT', ]],
['PPFD_DIF', ['PPFD_DIF', ]],
['APAR', ['APAR', ]],
['T_CANOPY', ['T_CANOPY', 'TC', 'Tc']],
['T_BOLE', ['T_BOLE', ]],
['TAU', ['TAU', ]],
['FETCH_FILTER', ['FETCH_FILTER', 'QcFoot']],
]


QC_FULL_DIRECT_D = {i[0]:i[1] for i in QC_VARIABLE_LIST_FULL_MAP}

QC_FULL_D = {}
for pair in QC_VARIABLE_LIST_FULL_MAP:
    for old_e in pair[1]:
        if old_e in QC_FULL_D:
            raise ONEFluxError("Duplicate old entry: '{e}'".format(e=old_e))
        else:
            QC_FULL_D[old_e] = pair[0]


# Will generate ERRORs in log
VARIABLE_LIST_MUST_BE_PRESENT = [
    'TA_F_MDS', 'TA_F_MDS_QC', 'TA_ERA', 'TA_F', 'TA_F_QC', 'SW_IN_F_MDS', 'SW_IN_F_MDS_QC',
    'SW_IN_ERA', 'SW_IN_F', 'SW_IN_F_QC', 'LW_IN_ERA', 'LW_IN_F', 'LW_IN_F_QC', 'VPD_F_MDS', 'VPD_F_MDS_QC',
    'VPD_ERA', 'VPD_F', 'VPD_F_QC', 'PA_ERA', 'PA_F', 'PA_F_QC', 'P_ERA', 'P_F', 'P_F_QC',
    'WS_ERA', 'WS_F', 'WS_F_QC', 'USTAR', 'NETRAD',
    'LE_F_MDS', 'LE_F_MDS_QC', 'LE_CORR', 'LE_RANDUNC', 'H_F_MDS', 'H_F_MDS_QC', 'H_CORR', 'H_RANDUNC',
    'NEE_VUT_REF', 'NEE_VUT_REF_QC', 'NEE_VUT_REF_RANDUNC',
    'RECO_NT_VUT_REF', 'GPP_NT_VUT_REF', 'RECO_DT_VUT_REF', 'GPP_DT_VUT_REF',
   ] + \
   ['NEE_VUT_{n}'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
   ['NEE_VUT_{n}_QC'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
   ['RECO_NT_VUT_{n}'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
   ['GPP_NT_VUT_{n}'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
   ['RECO_DT_VUT_{n}'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
   ['GPP_DT_VUT_{n}'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']]

# Will generate WARNINGs in log -- check should really be by resolution,
#                                  as some of these only appear for certain resolutions
VARIABLE_LIST_SHOULD_BE_PRESENT = [
    'LW_IN_F_MDS', 'LW_IN_F_MDS_QC', 'LW_IN_JSB', 'LW_IN_JSB_QC', 'LW_IN_JSB_ERA', 'LW_IN_JSB_F', 'LW_IN_JSB_F_QC',
    'CO2_F_MDS', 'CO2_F_MDS_QC', 'G_F_MDS', 'G_F_MDS_QC', 'EBC_CF_N', 'EBC_CF_METHOD',
    ]

# Will generate INFOs in log -- some variables might be missing from original data but for others,
#                               the check should really be by resolution,
#                               as some of these only appear for certain resolutions
VARIABLE_LIST_COULD_BE_PRESENT = [
    'USTAR_QC', 'NETRAD_QC', 'PPFD_IN', 'PPFD_IN_QC', 'PPFD_DIF', 'PPFD_DIF_QC', 'PPFD_OUT', 'PPFD_OUT_QC',
    'SW_DIF', 'SW_DIF_QC', 'SW_OUT', 'SW_OUT_QC', 'LW_OUT', 'LW_OUT_QC', 'PA', 'SW_IN_POT', 'P', 'WS', 'WD', 'RH',
    'LE_CORR_25', 'LE_CORR_75', 'LE_RANDUNC_METHOD', 'LE_RANDUNC_N', 'LE_CORR_JOINTUNC',
    'H_CORR_25', 'H_CORR_75', 'H_RANDUNC_METHOD', 'H_RANDUNC_N', 'H_CORR_JOINTUNC',
    'NEE_CUT_REF', 'NEE_CUT_REF_QC', 'NEE_CUT_REF_RANDUNC',
    'RECO_NT_CUT_REF', 'GPP_NT_CUT_REF', 'RECO_DT_CUT_REF', 'GPP_DT_CUT_REF',
    'RECO_SR', 'RECO_SR_N',
    ] + \
   ['TS_F_MDS_{n}'.format(n=i) for i in range(1, 20)] + \
   ['TS_F_MDS_{n}_QC'.format(n=i) for i in range(1, 20)] + \
   ['SWC_F_MDS_{n}'.format(n=i) for i in range(1, 20)] + \
   ['SWC_F_MDS_{n}_QC'.format(n=i) for i in range(1, 20)] + \
   ['NEE_CUT_{n}'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
   ['NEE_CUT_{n}_QC'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
   ['RECO_NT_CUT_{n}'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
   ['GPP_NT_CUT_{n}'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
   ['RECO_DT_CUT_{n}'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']] + \
   ['GPP_DT_CUT_{n}'.format(n=i) for i in ['05', '16', '25', '50', '75', '84', '95']]

