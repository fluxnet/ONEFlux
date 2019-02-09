'''
oneflux.pipeline.aux_info_files

For license information:
see LICENSE file or headers in oneflux.__init__.py 

Handling of auxiliary and info files

NOTES:
----- ID defines parameters-timestamps combinations relevant for a Variable see guidelines www.europe-fluxdata.eu, getting data
  ----- FORMAT for info files
        -- METEO
        ID, VAR, PAR, VALUE, DATE
        1,TA,ERA_SLOPE,3.1, -9999
        1,TA,ERA_INTER,1.1, -9999
        1,TA,ERA_RMSE,2.1, -9999
        1,TA,ERA_CORR,2.1, -9999
        2,SW_IN,ERA_SLOPE,2.1, -9999

        -- NEE (preferred format)
        ID, VAR, PAR, VALUE, DATE
        1, NEE_CUT_USTAR50, USTAR_THRESHOLD, 1.1, -9999
        2, NEE_VUT_USTAR50, USTAR_THRESHOLD, 1.1, 2010
        2, NEE_VUT_USTAR50, USTAR_THRESHOLD, 1.2, 2011
        3, NEE_VUT_REF, PERCENTILE, 46.25, 2010
        3, NEE_VUT_REF, USTAR_THRESHOLD, 2.1, 2010
        4, NEE_VUT_REF, PERCENTILE, 46.25, 2011
        4, NEE_VUT_REF, USTAR_THRESHOLD, 1.1, 2011
        5, RECO_NT_xxxx

        7, NEE_USTAR_THRESHOLD, CP_METHOD, 1, 2010
        7, NEE, CP_METHOD, 0, 2011

        8, CP_METHOD,USTAR_WORKED,0,2010
        8, CP_METHOD,USTAR_WORKED,1,2011
        9, MP_METHOD,USTAR_WORKED,1,2010

        10,CUT,PERCENTILE,1.75,-9999
        10,CUT,THRESHOLD,0.01,-9999
        ....
        11,VUT,PERCENTILE,1.75,2010
        11,VUT,THRESHOLD,0.01,2010
        12,VUT,PERCENTILE,3.25,2010
        12,VUT,THRESHOLD,0.01,2010


        ---- alternate format (used in BADM)
        ID, VAR, PAR, VALUE
        3, NEE_VUT_REF, PERCENTILE, 46.25
        3, NEE_VUT_REF, USTAR_THRESHOLD, 2.1
        3, NEE_VUT_REF, DATE, 2010
        4, NEE_VUT_REF, PERCENTILE, 46.75
        4, NEE_VUT_REF, USTAR_THRESHOLD, 2.05
        4, NEE_VUT_REF, DATE, 2011

@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2015-12-10
'''

import sys
import os
import logging
import re

from oneflux import ONEFluxError
from oneflux.utils.strings import is_int
from oneflux.pipeline.common import METEO_INFO, NEE_INFO, NEEDIR_PATTERN, NEE_PERC_USTAR_CUT_PATTERN, \
                                     NEE_PERC_USTAR_CUT, NEE_PERC_USTAR_VUT_PATTERN, NEE_PERC_USTAR_VUT, \
                                     UNC_INFO, UNC_INFO_ALT, PRODFILE_AUX_TEMPLATE, RESOLUTION_LIST, \
                                     MPDIR, CPDIR, test_pattern
from __builtin__ import enumerate

log = logging.getLogger(__name__)

AUX_HEADER = ['ID', 'VARIABLE', 'PARAMETER', 'VALUE', 'TIMESTAMP']
PERCENTILES = ['1.25', '3.75', '6.25', '8.75', '11.25', '13.75', '16.25', '18.75',
               '21.25', '23.75', '26.25', '28.75', '31.25', '33.75', '36.25', '38.75',
               '41.25', '43.75', '46.25', '48.75', '51.25', '53.75', '56.25', '58.75',
               '61.25', '63.75', '66.25', '68.75', '71.25', '73.75', '76.25', '78.75',
               '81.25', '83.75', '86.25', '88.75', '91.25', '93.75', '96.25', '98.75', '50']
PERCENTILES_SORTED = ['1.25', '3.75', '6.25', '8.75', '11.25', '13.75', '16.25', '18.75',
                      '21.25', '23.75', '26.25', '28.75', '31.25', '33.75', '36.25', '38.75',
                      '41.25', '43.75', '46.25', '48.75', '50.00', '51.25', '53.75', '56.25', '58.75',
                      '61.25', '63.75', '66.25', '68.75', '71.25', '73.75', '76.25', '78.75',
                      '81.25', '83.75', '86.25', '88.75', '91.25', '93.75', '96.25', '98.75']
FOUR_DIGIT_RE = re.compile("\D(\d{4})\D")


def generate_meteo(siteid, sitedir, first_year, last_year, version_data, version_processing, pipeline=None):
    log.debug("{s}: starting generation of AUXMETEO file".format(s=siteid))
    meteo_info = (METEO_INFO if pipeline is None else pipeline.meteo_info)
    prodfile_aux_template = (PRODFILE_AUX_TEMPLATE if pipeline is None else pipeline.prodfile_aux_template)

    filename = meteo_info.format(s=siteid, sd=sitedir, r='hh')
    if not os.path.isfile(filename):
        raise ONEFluxError("{s}: meteo info file not found: {f}".format(s=siteid, f=filename))

    H_BEGIN, H_END = "var", "corr"
    VAR_D = {
    'Ta': 'TA',
    'TA': 'TA',
    'Pa': 'PA',
    'PA': 'PA',
    'VPD': 'VPD',
    'WS': 'WS',
    'Precip': 'P',
    'P': 'P',
    'Rg': 'SW_IN',
    'SW_IN': 'SW_IN',
    'LWin': 'LW_IN',
    'LW_IN': 'LW_IN',
    'LWin_calc': 'LW_IN_JSB',
    'LW_IN_calc': 'LW_IN_JSB',
    }

    lines = []
    with open(filename, 'r') as f:
        lines = f.readlines()

    c_var, c_slope, c_intercept, c_rmse, c_corr = 0, 1, 2, 3, 4
    first_line = None
    for i, line in enumerate(lines):
        l = line.strip().lower()
        if l.startswith(H_BEGIN) and l.endswith(H_END):
            first_line = i
            break

    if first_line is None:
        raise ONEFluxError("{s}: first line of meteo info file not found: {f}".format(s=siteid, f=filename))
    if 'unit' in lines[first_line].lower():
        log.info("{s}: handling old format meteo info file: {f}".format(s=siteid, f=filename))
        c_slope, c_intercept, c_rmse, c_corr = 3, 4, 5, 6

    vars_l = ['TA', 'PA', 'VPD', 'WS', 'P', 'SW_IN', 'LW_IN', 'LW_IN_JSB']
    #pars_l = ['ERA_SLOPE', 'ERA_INTERCEPT', 'ERA_RMSE', 'ERA_CORRELATION']
    values = {i:None for i in vars_l}
    for line in lines[first_line + 1:first_line + 9]:
        l = line.strip().split(',')
        values[VAR_D[l[c_var]]] = [(float(l[c_slope].strip()) if (l[c_slope].strip() and l[c_slope].strip() != '-') else -9999),
                                   (float(l[c_intercept].strip()) if (l[c_intercept].strip() and l[c_intercept].strip() != '-') else -9999),
                                   (float(l[c_rmse].strip()) if (l[c_rmse].strip() and l[c_rmse].strip() != '-') else -9999),
                                   (float(l[c_corr].strip()) if (l[c_corr].strip() and l[c_corr].strip() != '-') else -9999),
                                  ]

    output_lines = [','.join(AUX_HEADER) + '\n']
    for i, var in enumerate(vars_l, start=1):
        if values[var] is None:
            raise ONEFluxError("{s}: ERA variable '{v}' not found in: {f}".format(s=siteid, v=var, f=filename))
        slope = ("{v:.2f}".format(v=values[var][0]) if values[var][0] != -9999 else '-9999')
        intercept = ("{v:.2f}".format(v=values[var][1]) if values[var][1] != -9999 else '-9999')
        rmse = ("{v:.2f}".format(v=values[var][2]) if values[var][2] != -9999 else '-9999')
        corr = ("{v:.2f}".format(v=values[var][3]) if values[var][3] != -9999 else '-9999')
        output_lines.append("{i},{v},{p},{val},{t}\n".format(i=i, v=var, p='ERA_SLOPE', val=slope, t='-9999'))
        output_lines.append("{i},{v},{p},{val},{t}\n".format(i=i, v=var, p='ERA_INTERCEPT', val=intercept, t='-9999'))
        output_lines.append("{i},{v},{p},{val},{t}\n".format(i=i, v=var, p='ERA_RMSE', val=rmse, t='-9999'))
        output_lines.append("{i},{v},{p},{val},{t}\n".format(i=i, v=var, p='ERA_CORRELATION', val=corr, t='-9999'))

    output_filename = prodfile_aux_template.format(s=siteid, sd=sitedir, aux='AUXMETEO', fy=first_year, ly=last_year, vd=version_data, vp=version_processing)
    log.info("{s}: writing auxiliary METEO file: {f}".format(s=siteid, f=output_filename))
    with open(output_filename, 'w') as f:
        f.writelines(output_lines)
    log.debug("{s}: finished generation of AUXMETEO file: {f}".format(s=siteid, f=output_filename))

    return output_filename


def load_csv_lines(filename):
    if not os.path.isfile(filename):
        return []
    with open(filename, 'r') as f:
        lines = f.readlines()
    output_lines = []
    for line in lines:
        l = line.strip().split(',')
        l = [i.strip() for i in l]
        output_lines.append(l)
    return output_lines

def get_created_ustar_years(mpdir, cpdir):
    mpfiles = [f for f in os.listdir(mpdir) if os.path.isfile(os.path.join(mpdir, f))]
    cpfiles = [f for f in os.listdir(cpdir) if os.path.isfile(os.path.join(cpdir, f))]

    mpyears_all = [FOUR_DIGIT_RE.findall(f) for f in mpfiles]
    mpyears_all = [i for i in mpyears_all if i]
    cpyears_all = [FOUR_DIGIT_RE.findall(f) for f in cpfiles]
    cpyears_all = [i for i in cpyears_all if i]

    for y_list in mpyears_all + cpyears_all:
        if len(y_list) != 1:
            raise ONEFluxError("Multiple years ({y}) found in MP/CP filenames: {f}".format(y=y_list, f=mpfiles + cpfiles))
        year = int(y_list[0])
        if 1900 > year > 2100:
            raise ONEFluxError("Year ({y}) out-of-range found in MP/CP filenames: {f}".format(y=year, f=mpfiles + cpfiles))
    mpyears = [int(l[0]) for l in mpyears_all]
    cpyears = [int(l[0]) for l in cpyears_all]

    return mpyears, cpyears

def load_ustar_cut(siteid, sitedir, first_year, last_year, nee_perc_ustar_cut_template=NEE_PERC_USTAR_CUT):
    nee_perc_ustar_cut = nee_perc_ustar_cut_template.format(s=siteid, sd=sitedir, fy=first_year, ly=last_year)
    log.debug("{s}: processing file: {f}".format(s=siteid, f=nee_perc_ustar_cut))
    nee_perc_ustar_cut_lines = load_csv_lines(filename=nee_perc_ustar_cut)
    if (last_year - first_year) < 2:
        if not nee_perc_ustar_cut_lines: log.warning("{s}: too few years, {e} file not created: {f}".format(s=siteid, e='NEE CUT USTAR percentiles', f=nee_perc_ustar_cut))
        nee_perc_ustar_cut_values = {k:'-9999' for i, k in enumerate(PERCENTILES) }
        nee_perc_ustar_cut_values['50.00'] = nee_perc_ustar_cut_values['50']
    else:
        if not nee_perc_ustar_cut_lines: raise ONEFluxError("{s}: {e} file not found: {f}".format(s=siteid, e='NEE CUT USTAR percentiles', f=nee_perc_ustar_cut))

        if (len(nee_perc_ustar_cut_lines) == 3 and not nee_perc_ustar_cut_lines[2].strip()) or len(nee_perc_ustar_cut_lines) > 2:
            raise ONEFluxError("{s}: NEE USTAR CUT file too many lines ({l}): {f}".format(s=siteid, l=len(nee_perc_ustar_cut_lines), f=nee_perc_ustar_cut))
        elif not (nee_perc_ustar_cut_lines[0][0].startswith(PERCENTILES[0]) and nee_perc_ustar_cut_lines[0][-1].strip().endswith(PERCENTILES[-1])):
            raise ONEFluxError("{s}: NEE USTAR CUT bad headers ({h}): {f}".format(s=siteid, h=nee_perc_ustar_cut_lines[0], f=nee_perc_ustar_cut))
        nee_perc_ustar_cut_values = {k:nee_perc_ustar_cut_lines[1][i].strip() for i, k in enumerate(PERCENTILES) }
        nee_perc_ustar_cut_values['50.00'] = nee_perc_ustar_cut_values['50']
    return nee_perc_ustar_cut_values

def load_ustar_vut(siteid, sitedir, year_range, nee_perc_ustar_vut_template=NEE_PERC_USTAR_VUT):
    nee_perc_ustar_vut = nee_perc_ustar_vut_template.format(s=siteid, sd=sitedir)
    log.debug("{s}: processing file: {f}".format(s=siteid, f=nee_perc_ustar_vut))
    nee_perc_ustar_vut_lines = load_csv_lines(filename=nee_perc_ustar_vut)
    if not nee_perc_ustar_vut_lines: raise ONEFluxError("{s}: {e} file not found: {f}".format(s=siteid, e='NEE VUT USTAR percentiles', f=nee_perc_ustar_vut))

    nee_perc_ustar_vut_values = {i:{} for i in year_range}
    if not ((nee_perc_ustar_vut_lines[0][0].lower().startswith('timestamp') or\
             nee_perc_ustar_vut_lines[0][0].lower().startswith('isodate') or\
             nee_perc_ustar_vut_lines[0][0].lower().startswith('year')) and\
            nee_perc_ustar_vut_lines[0][-1].endswith(PERCENTILES[-1])):
        raise ONEFluxError("{s}: NEE USTAR VUT bad headers ({h}): {f}".format(s=siteid, h=nee_perc_ustar_vut_lines[0], f=nee_perc_ustar_vut))
    elif (int(nee_perc_ustar_vut_lines[1][0]) != year_range[0]) or (int(nee_perc_ustar_vut_lines[-1][0]) != year_range[-1]):
        raise ONEFluxError("{s}: NEE USTAR VUT incompatible year range data=({d}), info=({i})".format(s=siteid, d="{f}-{l}".format(f=nee_perc_ustar_vut_lines[1][0], l=nee_perc_ustar_vut_lines[-1][0]), i="{f}-{l}".format(f=year_range[0], l=year_range[-1])))
    for y, year in enumerate(year_range):
        nee_perc_ustar_vut_values[year] = {k:nee_perc_ustar_vut_lines[y + 1][i + 1].strip() for i, k in enumerate(PERCENTILES) }
        nee_perc_ustar_vut_values[year]['50.00'] = nee_perc_ustar_vut_values[year]['50']
    return nee_perc_ustar_vut_values

def generate_nee(datadir, siteid, sitedir, first_year, last_year, version_data, version_processing, pipeline=None):
    log.debug("{s}: starting generation of AUXNEE file".format(s=siteid))

    nee_info_template = (NEE_INFO if pipeline is None else pipeline.nee_info)
    unc_info_template = (UNC_INFO if pipeline is None else pipeline.unc_info)
    unc_info_alt_template = (UNC_INFO_ALT if pipeline is None else pipeline.unc_info_alt)
    prodfile_aux_template = (PRODFILE_AUX_TEMPLATE if pipeline is None else pipeline.prodfile_aux_template)
    mpdir_template = (MPDIR if pipeline is None else pipeline.mpdir)
    cpdir_template = (CPDIR if pipeline is None else pipeline.cpdir)
    nee_perc_ustar_cut_template = (NEE_PERC_USTAR_CUT if pipeline is None else pipeline.nee_perc_ustar_cut)
    nee_perc_ustar_vut_template = (NEE_PERC_USTAR_VUT if pipeline is None else pipeline.nee_perc_ustar_vut)

    ### TEST year range for real range. Some sites have only energy/water fluxes for some of the first or last years, so NEE has shorter range
    nee_perc_ustar_cut = nee_perc_ustar_cut_template.format(s=siteid, sd=sitedir, fy=first_year, ly=last_year)
    if os.path.isfile(nee_perc_ustar_cut):
        find_nee_perc_ustar_cut = test_pattern(tdir=os.path.join(datadir, sitedir, NEEDIR_PATTERN), tpattern=NEE_PERC_USTAR_CUT_PATTERN.format(s=siteid, sd=sitedir, fy='????', ly='????'), label='aux_info_files', log_only=True)
        if len(find_nee_perc_ustar_cut) == 1:
            log.warning("{s}: USTAR CUT percentiles file FOUND: {f}".format(s=siteid, f=find_nee_perc_ustar_cut))
            find_nee_perc_ustar_cut = find_nee_perc_ustar_cut[0]
            _, find_first_year, find_last_year, _ = find_nee_perc_ustar_cut.split('_', 3)
            if find_first_year != first_year:
                log.error("{s}: first year ({fy1}) differs from USTAR CUT percentiles file first year ({fy2}: {f}".format(s=siteid, f=find_nee_perc_ustar_cut, fy1=first_year, fy2=find_first_year))
            if find_last_year != last_year:
                log.error("{s}: last year ({fy1}) differs from USTAR CUT percentiles file last year ({fy2}: {f}".format(s=siteid, f=find_nee_perc_ustar_cut, fy1=last_year, fy2=find_last_year))
            first_year, last_year = int(first_year), int(last_year)
        else:
            log.warning("{s}: incorrect number of NEE_PERC_USTAR_CUT files found (1-2 years record?): {l}".format(s=siteid, l=find_nee_perc_ustar_cut))
    else:
        log.warning("{s}: looking for alternate USTAR CUT percentiles file, NOT found: {f}".format(s=siteid, f=nee_perc_ustar_cut))
        alt_nee_perc_ustar_cut = test_pattern(tdir=os.path.join(datadir, sitedir, NEEDIR_PATTERN), tpattern=NEE_PERC_USTAR_CUT_PATTERN.format(s=siteid, sd=sitedir, fy='????', ly='????'), label='aux_info_files', log_only=True)
        if len(alt_nee_perc_ustar_cut) == 1:
            log.warning("{s}: alternate USTAR CUT percentiles file FOUND: {f}".format(s=siteid, f=alt_nee_perc_ustar_cut))
            alt_nee_perc_ustar_cut = alt_nee_perc_ustar_cut[0]
            _, first_year, last_year, _ = alt_nee_perc_ustar_cut.split('_', 3)
            first_year, last_year = int(first_year), int(last_year)
        else:
            log.warning("{s}: incorrect number of alternate NEE_PERC_USTAR_CUT files found (1-2 years record?): {l}".format(s=siteid, l=alt_nee_perc_ustar_cut))

#        # PREVIOU SINGLE YEAR IMPLEMENTATION
#        alt_nee_perc_ustar_cut = NEE_PERC_USTAR_CUT.format(s=siteid, sd=sitedir, fy=int(first_year) + 1, ly=last_year)
#        if os.path.isfile(alt_nee_perc_ustar_cut):
#            log.warning("{s}: alternate USTAR CUT percentiles file FOUND: {f}".format(s=siteid, f=alt_nee_perc_ustar_cut))
#            first_year += 1
#        else:
#            log.error("{s}: alternate USTAR CUT percentiles file NOT found: {f}".format(s=siteid, f=alt_nee_perc_ustar_cut))

    year_range = range(int(first_year), int(last_year) + 1)

    ### process NEE USTAR CUT
    nee_perc_ustar_cut_values = load_ustar_cut(siteid=siteid, sitedir=sitedir, first_year=first_year, last_year=last_year, nee_perc_ustar_cut_template=nee_perc_ustar_cut_template)

    ### process NEE USTAR VUT
    nee_perc_ustar_vut_values = load_ustar_vut(siteid=siteid, sitedir=sitedir, year_range=year_range, nee_perc_ustar_vut_template=nee_perc_ustar_vut_template)

    # process NEE, RECO, and GPP info
    u50_ustar_perc = dict({'CUT':nee_perc_ustar_cut_values['50.00']}.items() + {year:threshold['50.00'] for year, threshold in nee_perc_ustar_vut_values.iteritems()}.items())
    nee_ref_ustar_perc = {i:{} for i in RESOLUTION_LIST}
    unc_ref_ustar_perc = {i:{j:{} for j in RESOLUTION_LIST} for i in ['RECO_NT', 'GPP_NT', 'RECO_DT', 'GPP_DT']}
    ustar_not_working = {'files_mp':set(), 'files_cp':set(), 'info_mp':set(), 'info_cp':set()}

    lines = []
    for res in RESOLUTION_LIST:
        # process NEE
        nee_info = nee_info_template.format(s=siteid, sd=sitedir, r=res)
        method_line_num = None
        if not os.path.isfile(nee_info):
            raise ONEFluxError("NEE info file not found: {f}".format(f=nee_info))
        with open(nee_info, 'r') as f:
            lines = f.readlines()
        for line_num, line in enumerate(reversed(lines)):
            # NEE REF VUT
            if line.strip().lower().startswith('nee_ref_y'):
                year_extra = None
                unsplit_year = line.strip().lower().split('on year')
                if len(unsplit_year) == 2:
                    year = int(unsplit_year[1].strip().split()[0].strip())
                elif len(unsplit_year) == 1 and len(year_range) == 1:
                    year = first_year
                elif len(unsplit_year) == 1 and len(year_range) == 2:
                    year = first_year
                    year_extra = last_year
                else:
                    raise ONEFluxError("{s}: Unknown NEE VUT REF percentile/threshold entry in line: '{l}'".format(s=siteid, l=line.strip()))
                threshold = line.strip().lower().split('ustar percentile')[1].strip().split()[0].strip()
                ustar = nee_perc_ustar_vut_values[year][threshold]
                if nee_ref_ustar_perc[res].has_key(year):
                    raise ONEFluxError("{s} duplicated entry for NEE REF VUT USTAR: {f}".format(s=siteid, f=nee_info))
                else:
                    nee_ref_ustar_perc[res][year] = (threshold, ustar)
                if year_extra:
                    if nee_ref_ustar_perc[res].has_key(year_extra):
                        raise ONEFluxError("{s} duplicated entry for NEE REF VUT USTAR: {f}".format(s=siteid, f=nee_info))
                    else:
                        nee_ref_ustar_perc[res][year_extra] = (threshold, ustar)
                        year_extra = None
#                print 'VUT', res, year, threshold, ustar
            # NEE REF CUT
            elif line.strip().lower().startswith('nee_ref_c'):
                threshold = line.strip().lower().split('ustar percentile')[1].strip().split()[0].strip()
                ustar = nee_perc_ustar_cut_values[threshold]
                if nee_ref_ustar_perc[res].has_key('CUT'):
                    raise ONEFluxError("{s} duplicated entry for NEE REF CUT USTAR: {f}".format(s=siteid, f=nee_info))
                else:
                    nee_ref_ustar_perc[res]['CUT'] = (threshold, ustar)
#                print 'CUT', res, threshold, ustar
            # USTAR-method-not-working entries start
            elif ('year' in line.strip().lower()) and ('method not applied' in line.strip().lower()):
                if method_line_num is not None:
                    raise ONEFluxError('Two lines (#{l1} and #{l2}) starting with info for USTAR method not working: {f}'.format(l1=method_line_num, l2=len(lines) - line_num - 1, f=nee_info))
                method_line_num = len(lines) - line_num - 1

        # USTAR-method-not-working entries detect
        if method_line_num:
            lnum = method_line_num
            while lnum < len(lines):
                if is_int(lines[lnum].strip()[:4]):
                    if lines[lnum].strip().lower().endswith('mp'):
                        ustar_not_working['info_mp'].add(int(lines[lnum].strip()[:4]))
#                        print lines[lnum].strip()
                    elif lines[lnum].strip().lower().endswith('cp'):
                        ustar_not_working['info_cp'].add(int(lines[lnum].strip()[:4]))
#                        print lines[lnum].strip()
                lnum += 1
        else:
            log.warning('USTAR-method-not-working entries not found at {r} for: {f}'.format(r=res.upper(), f=nee_info))

        # USTAR-method-not-working files detect
        mpyears, cpyears = get_created_ustar_years(mpdir=mpdir_template.format(sd=sitedir), cpdir=cpdir_template.format(sd=sitedir))
        ustar_not_working['files_mp'] = set(year_range) - set(mpyears)
        ustar_not_working['files_cp'] = set(year_range) - set(cpyears)
#        print 'MP: ', mpyears
#        print 'CP: ', cpyears
#        print

        # process RECO, GPP
        for method, variable in [('NT', 'RECO'), ('NT', 'GPP'), ('DT', 'RECO'), ('DT', 'GPP')]:
            key = variable + '_' + method
            unc_info = unc_info_template.format(s=siteid, sd=sitedir, m=method, v=variable, r=res)
            if not os.path.isfile(unc_info):
                unc_info = unc_info_alt_template.format(s=siteid, sd=sitedir, m=method, v=variable, r=res)
                if not os.path.isfile(unc_info):
                    raise ONEFluxError("UNC info file not found: {f}".format(f=unc_info))
            log.debug("{s}: processing file: {f}".format(s=siteid, f=unc_info))
            with open(unc_info, 'r') as f:
                lines = f.readlines()
            for line in reversed(lines):
                # RECO/GPP REF VUT
                if line.strip().lower().startswith('{v}_ref_y'.format(v=variable).lower()):
                    year_extra = None
                    unsplit_year = line.strip().lower().split('on year')
                    if len(unsplit_year) == 2:
                        year = int(unsplit_year[1].strip().split()[0].strip())
                    elif len(unsplit_year) == 1 and len(year_range) == 1:
                        year = first_year
                    elif len(unsplit_year) == 1 and len(year_range) == 2:
                        year = first_year
                        year_extra = last_year
                    else:
                        raise ONEFluxError("{s}: Unknown RECO/GPP VUT REF percentile/threshold entry in line: '{l}'".format(s=siteid, l=line.strip()))
                    threshold = line.strip().lower().split('ustar percentile')[1].strip().split()[0].strip()
                    ustar = (nee_perc_ustar_vut_values[year][threshold] if nee_perc_ustar_vut_values.has_key(year) else -9999)
                    if unc_ref_ustar_perc[key][res].has_key(year):
                        raise ONEFluxError("{s} duplicated entry for {v} REF VUT USTAR: {f}".format(s=siteid, f=nee_info, v=variable))
                    else:
                        unc_ref_ustar_perc[key][res][year] = (threshold, ustar)
                    if year_extra:
                        if unc_ref_ustar_perc[key][res].has_key(year_extra):
                            raise ONEFluxError("{s} duplicated entry for RECO/GPP REF VUT USTAR: {f}".format(s=siteid, f=nee_info))
                        else:
                            unc_ref_ustar_perc[key][res][year_extra] = (threshold, ustar)
                            year_extra = None
#                    print variable, method, 'VUT', res, year, threshold, ustar
                # RECO/GPP REF CUT
                elif line.strip().lower().startswith('{v}_ref_c'.format(v=variable).lower()):
                    threshold = line.strip().lower().split('ustar percentile')[1].strip().split()[0].strip()
                    ustar = nee_perc_ustar_cut_values[threshold]
                    if unc_ref_ustar_perc[key][res].has_key('CUT'):
                        raise ONEFluxError("{s} duplicated entry for {v} REF CUT USTAR: {f}".format(s=siteid, f=nee_info, v=variable))
                    else:
                        unc_ref_ustar_perc[key][res]['CUT'] = (threshold, ustar)
#                    print variable, method, 'CUT', res, threshold, ustar

    output_lines = [','.join(AUX_HEADER) + '\n']

    # output USTAR not working
    entry_number = 1
    for year in year_range:
        if year in ustar_not_working['files_mp']:
            nline = "{i},USTAR_MP_METHOD,SUCCESS_RUN,0,{y}\n".format(i=entry_number, y=year)
            if year not in ustar_not_working['info_mp']:
                log.warning("{s}: USTAR_MP, year {y} not found in files, but success in info".format(s=siteid, y=year))
        else:
            nline = "{i},USTAR_MP_METHOD,SUCCESS_RUN,1,{y}\n".format(i=entry_number, y=year)
            if year in ustar_not_working['info_mp']:
                log.error("{s}: USTAR_MP, year {y} failed in info, but found in files".format(s=siteid, y=year))
        output_lines.append(nline)

    entry_number += 1
    for year in year_range:
        if year in ustar_not_working['files_cp']:
            nline = "{i},USTAR_CP_METHOD,SUCCESS_RUN,0,{y}\n".format(i=entry_number, y=year)
            if year not in ustar_not_working['info_cp']:
                log.warning("{s}: USTAR_CP, year {y} not found in files, but success in info".format(s=siteid, y=year))
        else:
            nline = "{i},USTAR_CP_METHOD,SUCCESS_RUN,1,{y}\n".format(i=entry_number, y=year)
            if year in ustar_not_working['info_cp']:
                log.error("{s}: USTAR_CP, year {y} failed in info, but found in files".format(s=siteid, y=year))
        output_lines.append(nline)

    # output USTAR_THRESHOLD_50
    entry_number += 1
    nline = "{i},NEE_CUT_USTAR50,USTAR_THRESHOLD,{v},-9999\n".format(i=entry_number, v=u50_ustar_perc.get('CUT', -9999))
    output_lines.append(nline)
    entry_number += 1
    for year in year_range:
        nline = "{i},NEE_VUT_USTAR50,USTAR_THRESHOLD,{v},{y}\n".format(i=entry_number, v=u50_ustar_perc.get(year, -9999), y=year)
        output_lines.append(nline)

    # output NEE REF
    for res in RESOLUTION_LIST:
        entry_number += 1
        perc, thres = nee_ref_ustar_perc[res].get('CUT', (-9999, -9999))
        nline = "{i},NEE_CUT_REF,{r}_USTAR_PERCENTILE,{v},-9999\n".format(i=entry_number, r=res.upper(), v=perc)
        output_lines.append(nline)
        nline = "{i},NEE_CUT_REF,{r}_USTAR_THRESHOLD,{v},-9999\n".format(i=entry_number, r=res.upper(), v=thres)
        output_lines.append(nline)
        entry_number += 1
        for year in year_range:
            perc, thres = nee_ref_ustar_perc[res].get(year, (-9999, -9999))
            nline = "{i},NEE_VUT_REF,{r}_USTAR_PERCENTILE,{v},{y}\n".format(i=entry_number, r=res.upper(), v=perc, y=year)
            output_lines.append(nline)
            nline = "{i},NEE_VUT_REF,{r}_USTAR_THRESHOLD,{v},{y}\n".format(i=entry_number, r=res.upper(), v=thres, y=year)
            output_lines.append(nline)

    # output UNC REF
    for prod in ['RECO_NT', 'GPP_NT', 'RECO_DT', 'GPP_DT']:
        for res in RESOLUTION_LIST:
            entry_number += 1
            perc, thres = unc_ref_ustar_perc[prod][res].get('CUT', (-9999, -9999))
            nline = "{i},{p}_CUT_REF,{r}_USTAR_PERCENTILE,{v},-9999\n".format(i=entry_number, p=prod, r=res.upper(), v=perc)
            output_lines.append(nline)
            nline = "{i},{p}_CUT_REF,{r}_USTAR_THRESHOLD,{v},-9999\n".format(i=entry_number, p=prod, r=res.upper(), v=thres)
            output_lines.append(nline)
            entry_number += 1
            for year in year_range:
                perc, thres = unc_ref_ustar_perc[prod][res].get(year, (-9999, -9999))
                nline = "{i},{p}_VUT_REF,{r}_USTAR_PERCENTILE,{v},{y}\n".format(i=entry_number, p=prod, r=res.upper(), v=perc, y=year)
                output_lines.append(nline)
                nline = "{i},{p}_VUT_REF,{r}_USTAR_THRESHOLD,{v},{y}\n".format(i=entry_number, p=prod, r=res.upper(), v=thres, y=year)
                output_lines.append(nline)

    # output CUT thresholds
    for perc in PERCENTILES_SORTED:
        entry_number += 1
        thres = nee_perc_ustar_cut_values[perc]
        nline = "{i},USTAR_CUT,USTAR_PERCENTILE,{v},-9999\n".format(i=entry_number, v=perc)
        output_lines.append(nline)
        nline = "{i},USTAR_CUT,USTAR_THRESHOLD,{v},-9999\n".format(i=entry_number, v=thres)
        output_lines.append(nline)

    # output VUT thresholds
    for year in year_range:
        for perc in PERCENTILES_SORTED:
            entry_number += 1
            thres = nee_perc_ustar_vut_values[year][perc]
            nline = "{i},USTAR_VUT,USTAR_PERCENTILE,{v},{y}\n".format(i=entry_number, v=perc, y=year)
            output_lines.append(nline)
            nline = "{i},USTAR_VUT,USTAR_THRESHOLD,{v},{y}\n".format(i=entry_number, v=thres, y=year)
            output_lines.append(nline)

    output_filename = prodfile_aux_template.format(s=siteid, sd=sitedir, aux='AUXNEE', fy=first_year, ly=last_year, vd=version_data, vp=version_processing)
    log.info("{s}: writing auxiliary NEE file: {f}".format(s=siteid, f=output_filename))
    with open(output_filename, 'w') as f:
        f.writelines(output_lines)
    log.debug("{s}: finished generation of AUXNEE file: {f}".format(s=siteid, f=output_filename))

    return output_filename

# TODO: Make AUX files Tier aware..........

def run_site_aux(datadir, siteid, sitedir, first_year, last_year, version_data, version_processing, pipeline=None):
    log.info("Starting generation of AUX-INFO files for {s}".format(s=siteid))

    aux_file_list = []
    aux_file_list.append(generate_meteo(siteid=siteid, sitedir=sitedir, first_year=first_year, last_year=last_year, version_data=version_data, version_processing=version_processing, pipeline=pipeline))
    aux_file_list.append(generate_nee(datadir=datadir, siteid=siteid, sitedir=sitedir, first_year=first_year, last_year=last_year, version_data=version_data, version_processing=version_processing, pipeline=pipeline))

    log.info("Finished generation of AUX-INFO files for {s}".format(s=siteid))
    return aux_file_list

if __name__ == '__main__':
    sys.exit("ERROR: cannot run independently")
