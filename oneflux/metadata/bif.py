'''
oneflux.metadata.bif

For license information:
see LICENSE file or headers in oneflux.__init__.py 

General BIF metadata handling functions for ONEFlux

@author: Carlo Trotta
@contact: trottacarlo@unitus.it
@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2025-10-30

EXAMPLE USAGE:

python BIFONEFlux.py \
--path_file_pipeline /home/c.trotta/ONEFluxBIF/ONEFLUX_US-xNG/ONEFlux_pipeline_US-xNG__RoundRobin2_202510240903.log \
--path_00_fp /home/c.trotta/ONEFluxBIF/ONEFLUX_US-xNG/00_fp_dataset \
--path_AUXMETEO /home/c.trotta/ONEFluxBIF/ONEFLUX_US-xNG/99_fluxnet2015/FLX_US-xNG_FLUXNET_AUXMETEO_2019-2024_1-5.csv \
--path_AUXNEE /home/c.trotta/ONEFluxBIF/ONEFLUX_US-xNG/99_fluxnet2015/FLX_US-xNG_FLUXNET_AUXNEE_2019-2024_1-5.csv \
--path_file_data_dd /home/c.trotta/ONEFluxBIF/ONEFLUX_US-xNG/99_fluxnet2015/FLX_US-xNG_FLUXNET_FULLSET_DD_2019-2024_1-5.csv \
--path_file_data_hh /home/c.trotta/ONEFluxBIF/ONEFLUX_US-xNG/99_fluxnet2015/FLX_US-xNG_FLUXNET_FULLSET_HH_2019-2024_1-5.csv \
--path_file_data_mm /home/c.trotta/ONEFluxBIF/ONEFLUX_US-xNG/99_fluxnet2015/FLX_US-xNG_FLUXNET_FULLSET_MM_2019-2024_1-5.csv \
--path_file_data_ww /home/c.trotta/ONEFluxBIF/ONEFLUX_US-xNG/99_fluxnet2015/FLX_US-xNG_FLUXNET_FULLSET_WW_2019-2024_1-5.csv \
--path_file_data_yy /home/c.trotta/ONEFluxBIF/ONEFLUX_US-xNG/99_fluxnet2015/FLX_US-xNG_FLUXNET_FULLSET_YY_2019-2024_1-5.csv \
--path_output_varinfo_yy /home/c.trotta/ONEFluxBIF/ONEFLUX_US-xNG__BIFONE/VAR_INFO_BIF_US-xNG_YY.csv \
--path_output_varinfo_mm /home/c.trotta/ONEFluxBIF/ONEFLUX_US-xNG__BIFONE/VAR_INFO_BIF_US-xNG_MM.csv \
--path_output_varinfo_ww /home/c.trotta/ONEFluxBIF/ONEFLUX_US-xNG__BIFONE/VAR_INFO_BIF_US-xNG_WW.csv \
--path_output_varinfo_dd /home/c.trotta/ONEFluxBIF/ONEFLUX_US-xNG__BIFONE/VAR_INFO_BIF_US-xNG_DD.csv \
--path_output_varinfo_hh /home/c.trotta/ONEFluxBIF/ONEFLUX_US-xNG__BIFONE/VAR_INFO_BIF_US-xNG_HH.csv \
--path_bif_other /home/c.trotta/ONEFluxBIF/ONEFLUX_US-xNG/BIF_US-xNG_20251022.csv \
--path_file_varinfo /home/c.trotta/ONEFluxBIF/ONEFLUX_US-xNG/VAR_INFO_US-xNG_BASE-10-5_20251022.csv \
--path_output_merge /home/c.trotta/ONEFluxBIF/ONEFLUX_US-xNG__BIFONE/GENERAL_BIF_US-xNG.csv


'path_AUXNEE': 'path of the AUXNEE file created by ONEFlux'
'path_AUXMETEO': 'path of the AUXMETEO filecreated by ONEFlux'
'path_00_fp': 'path of the 00_fp_dataset folder'
'path_file_pipeline': 'path of the ONEFlux_pipeline*.log file'
'path_output_merge': 'path of destination file to merge BIF from AUX and other'
'path_output_varinfo_yy': 'path of destination directory (YY)'
'path_output_varinfo_mm': 'path of destination directory (MM)'
'path_output_varinfo_ww': 'path of destination directory (WW)'
'path_output_varinfo_dd': 'path of destination directory (DD)'
'path_output_varinfo_hh': 'path of destination directory (HH)'    
'path_file_varinfo': 'path of the file VARINFO_*'
'path_file_data_yy': 'path of the file data YY'
'path_file_data_mm': 'path of the file data MM'
'path_file_data_ww': 'path of the file data WW'
'path_file_data_dd': 'path of the file data DD'
'path_file_data_hh': 'path of the file data HH'
'path_file_definitions_yy': 'path of the file with varinfo definitions (YY) (default is %s)' % DEFINITION_YY
'path_file_definitions_mm': 'path of the file with varinfo definitions (MM) (default is %s)' % DEFINITION_MM
'path_file_definitions_ww': 'path of the file with varinfo definitions (WW) (default is %s)' % DEFINITION_WW
'path_file_definitions_dd': 'path of the file with varinfo definitions (DD) (default is %s)' % DEFINITION_DD
'path_file_definitions_hh': 'path of the file with varinfo definitions (HH) (default is %s)' % DEFINITION_HH    
'path_bif_other': 'path folder(s) of BIF to merge'
'''

import os
import pandas as pd
import logging

from oneflux.metadata.bif_var_info import run_var_info
from oneflux.metadata.bif_aux import run_bif_aux

log = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

DEFINITION_HH = os.path.join(SCRIPT_DIR, 'var_info_definitions_hh.txt')
DEFINITION_DD = os.path.join(SCRIPT_DIR, 'var_info_definitions_dd.txt')
DEFINITION_WW = os.path.join(SCRIPT_DIR, 'var_info_definitions_ww.txt')
DEFINITION_MM = os.path.join(SCRIPT_DIR, 'var_info_definitions_mm.txt')
DEFINITION_YY = os.path.join(SCRIPT_DIR, 'var_info_definitions_yy.txt')


def load_csv(filename):
    '''
    Load a CSV file into a pandas DataFrame
    trying for single double quotes or dual double quotes
    as escape characters.
    
    Parameters:
    filename (str): Path to the CSV file.
    
    Returns:
    pd.DataFrame: DataFrame containing the CSV data.
    '''
    try:
        df = pd.read_csv(filename)
    except pd.errors.ParserError as e:
        log.warning("Failed to parse CSV file {filename} with single double quotes, error: {e}".format(filename=filename, e=e))
        try:
            with open(filename, 'r') as f:
                log.warning("Loading file '{filename}', trying handle of dual double quotes".format(filename=filename))
                content = f.read()
                df = pd.read_csv(pd.compat.StringIO(content.replace('""', '"')))
        except pd.errors.ParserError as e:
            log.critical("Failed to parse CSV file {filename} with both escape characters.".format(filename=filename))
            raise e
    return df


def run_bif(path_file_varinfo, path_file_pipeline, path_00_fp,
            path_file_data_hh, path_file_data_dd, path_file_data_ww, path_file_data_mm, path_file_data_yy,
            path_output_varinfo_hh, path_output_varinfo_dd, path_output_varinfo_ww, path_output_varinfo_mm, path_output_varinfo_yy,
            path_aux_meteo, path_aux_nee, path_output_merge, zipfilename, path_bif_other=None
            ):
    
    log.info("Generating BIF VAR_INFO and AUX BIF files")
    msg = "Run BIF function using:"
    msg += "path_file_varinfo ({i})".format(i=path_file_varinfo)
    msg += ", path_file_pipeline ({i})".format(i=path_file_pipeline)
    msg += ", path_00_fp ({i})".format(i=path_00_fp)
    msg += ", path_file_data_hh ({i})".format(i=path_file_data_hh)
    msg += ", path_file_data_dd ({i})".format(i=path_file_data_dd)
    msg += ", path_file_data_ww ({i})".format(i=path_file_data_ww)
    msg += ", path_file_data_mm ({i})".format(i=path_file_data_mm)
    msg += ", path_file_data_yy ({i})".format(i=path_file_data_yy)
    msg += ", path_output_varinfo_hh ({i})".format(i=path_output_varinfo_hh)
    msg += ", path_output_varinfo_dd ({i})".format(i=path_output_varinfo_dd)
    msg += ", path_output_varinfo_ww ({i})".format(i=path_output_varinfo_ww)
    msg += ", path_output_varinfo_mm ({i})".format(i=path_output_varinfo_mm)
    msg += ", path_output_varinfo_yy ({i})".format(i=path_output_varinfo_yy)
    msg += ", path_aux_meteo ({i})".format(i=path_aux_meteo)
    msg += ", path_aux_nee ({i})".format(i=path_aux_nee)
    msg += ", path_output_merge ({i})".format(i=path_output_merge)
    msg += ", path_bif_other ({i})".format(i=path_bif_other)
    log.debug(msg)

    run_var_info(path_file_varinfo=path_file_varinfo, path_file_data=path_file_data_hh, path_00_fp=path_00_fp, path_file_definitions=DEFINITION_HH, path_file_pipeline=path_file_pipeline, path_file_output=path_output_varinfo_hh, zipfilename=zipfilename)
    run_var_info(path_file_varinfo=path_file_varinfo, path_file_data=path_file_data_dd, path_00_fp=path_00_fp, path_file_definitions=DEFINITION_DD, path_file_pipeline=path_file_pipeline, path_file_output=path_output_varinfo_dd, zipfilename=zipfilename)
    run_var_info(path_file_varinfo=path_file_varinfo, path_file_data=path_file_data_ww, path_00_fp=path_00_fp, path_file_definitions=DEFINITION_WW, path_file_pipeline=path_file_pipeline, path_file_output=path_output_varinfo_ww, zipfilename=zipfilename)
    run_var_info(path_file_varinfo=path_file_varinfo, path_file_data=path_file_data_mm, path_00_fp=path_00_fp, path_file_definitions=DEFINITION_MM, path_file_pipeline=path_file_pipeline, path_file_output=path_output_varinfo_mm, zipfilename=zipfilename)
    run_var_info(path_file_varinfo=path_file_varinfo, path_file_data=path_file_data_yy, path_00_fp=path_00_fp, path_file_definitions=DEFINITION_YY, path_file_pipeline=path_file_pipeline, path_file_output=path_output_varinfo_yy, zipfilename=zipfilename)
    # run_var_info(args['path_file_varinfo'], args['path_file_data_dd'], args['path_00_fp'], args['path_file_definitions_dd'], args['path_file_pipeline'], args['path_output_varinfo_dd'])
    # run_var_info(args['path_file_varinfo'], args['path_file_data_hh'], args['path_00_fp'], args['path_file_definitions_hh'], args['path_file_pipeline'], args['path_output_varinfo_hh'])    
    # run_var_info(args['path_file_varinfo'], args['path_file_data_dd'], args['path_00_fp'], args['path_file_definitions_dd'], args['path_file_pipeline'], args['path_output_varinfo_dd'])    
    # run_var_info(args['path_file_varinfo'], args['path_file_data_ww'], args['path_00_fp'], args['path_file_definitions_ww'], args['path_file_pipeline'], args['path_output_varinfo_ww'])
    # run_var_info(args['path_file_varinfo'], args['path_file_data_mm'], args['path_00_fp'], args['path_file_definitions_mm'], args['path_file_pipeline'], args['path_output_varinfo_mm'])    
    # run_var_info(args['path_file_varinfo'], args['path_file_data_yy'], args['path_00_fp'], args['path_file_definitions_yy'], args['path_file_pipeline'], args['path_output_varinfo_yy'])

    run_bif_aux(input_path_aux_meteo=path_aux_meteo, input_path_aux_nee=path_aux_nee, file_output_path=path_output_merge, path_file_pipeline=path_file_pipeline, zipfilename=zipfilename)
    # run_bif_aux(input_path_aux_meteo=args['path_AUXMETEO'], input_path_aux_nee=args['path_AUXNEE'], file_output_path=args['path_output_merge'], path_file_pipeline=args['path_file_pipeline'])

    # merge other to the path_output_merge file
    if path_bif_other is not None:
        to_merge = load_csv(path_output_merge)
        for bif_other in path_bif_other:
            log.info('open file: %s' % bif_other)
            df1 = load_csv(bif_other)
            log.info('original range GROUP_ID: %d %d' % (df1['GROUP_ID'].min(),df1['GROUP_ID'].max()))
            df1['GROUP_ID'] = df1['GROUP_ID'] + to_merge['GROUP_ID'].max()
            log.info('recalculated range GROUP_ID: %d %d' % (df1['GROUP_ID'].min(),df1['GROUP_ID'].max()))
            to_merge = pd.concat([to_merge,df1], ignore_index=True)
            to_merge.to_csv(path_output_merge, index=False)
        # reorder to merge
        # first GRP_ONEFLUX then OTHERs then ERA_DOWN, UST_THR, FLX_REF
        # print(to_merge.shape)
        GRP_ONEFLUX = to_merge.loc[(to_merge['VARIABLE_GROUP'] == 'GRP_ONEFLUX')].copy()
        to_merge.drop(to_merge.index[(to_merge['VARIABLE_GROUP'] == 'GRP_ONEFLUX')],inplace=True)
        ERA_DOWN = to_merge.loc[(to_merge['VARIABLE_GROUP'] == 'GRP_ERA_DOWN')].copy()
        to_merge.drop(to_merge.index[(to_merge['VARIABLE_GROUP'] == 'GRP_ERA_DOWN')],inplace=True)
        UST_THR = to_merge.loc[(to_merge['VARIABLE_GROUP'] == 'GRP_UST_THR')].copy()
        to_merge.drop(to_merge.index[(to_merge['VARIABLE_GROUP'] == 'GRP_UST_THR')],inplace=True)
        FLX_REF = to_merge.loc[(to_merge['VARIABLE_GROUP'] == 'GRP_FLUX_REF')].copy()
        to_merge.drop(to_merge.index[(to_merge['VARIABLE_GROUP'] == 'GRP_FLUX_REF')],inplace=True)
        # print(to_merge.shape)
        to_merge_reord = []
        cnt_grp_id = 0
        for grp_id in sorted(GRP_ONEFLUX['GROUP_ID'].unique()):
            suby = GRP_ONEFLUX.loc[(GRP_ONEFLUX['GROUP_ID'] == grp_id)].copy()
            cnt_grp_id = cnt_grp_id + 1
            log.info('VARIABLE_GROUP: %s; GROUP_ID: %d (old); %d (new)' % (suby['VARIABLE_GROUP'].unique(),grp_id,cnt_grp_id))
            suby['GROUP_ID'] = cnt_grp_id
            to_merge_reord.append(suby)
        for grp_id in sorted(to_merge['GROUP_ID'].unique()):
            suby = to_merge.loc[(to_merge['GROUP_ID'] == grp_id)].copy()
            cnt_grp_id = cnt_grp_id + 1
            log.info('VARIABLE_GROUP: %s; GROUP_ID: %d (old); %d (new)' % (suby['VARIABLE_GROUP'].unique(),grp_id,cnt_grp_id))
            suby['GROUP_ID'] = cnt_grp_id
            to_merge_reord.append(suby)
        for grp_id in sorted(ERA_DOWN['GROUP_ID'].unique()):
            suby = ERA_DOWN.loc[(ERA_DOWN['GROUP_ID'] == grp_id)].copy()
            cnt_grp_id = cnt_grp_id + 1
            log.info('VARIABLE_GROUP: %s; GROUP_ID: %d (old); %d (new)' % (suby['VARIABLE_GROUP'].unique(),grp_id,cnt_grp_id))
            suby['GROUP_ID'] = cnt_grp_id
            to_merge_reord.append(suby)
        for grp_id in sorted(UST_THR['GROUP_ID'].unique()):
            suby = UST_THR.loc[(UST_THR['GROUP_ID'] == grp_id)].copy()
            cnt_grp_id = cnt_grp_id + 1
            log.info('VARIABLE_GROUP: %s; GROUP_ID: %d (old); %d (new)' % (suby['VARIABLE_GROUP'].unique(),grp_id,cnt_grp_id))
            suby['GROUP_ID'] = cnt_grp_id
            to_merge_reord.append(suby)
        for grp_id in sorted(FLX_REF['GROUP_ID'].unique()):
            suby = FLX_REF.loc[(FLX_REF['GROUP_ID'] == grp_id)].copy()
            cnt_grp_id = cnt_grp_id + 1
            log.info('VARIABLE_GROUP: %s; GROUP_ID: %d (old); %d (new)' % (suby['VARIABLE_GROUP'].unique(),grp_id,cnt_grp_id))
            suby['GROUP_ID'] = cnt_grp_id
            to_merge_reord.append(suby)
        to_merge_reord = pd.concat(to_merge_reord,ignore_index=True)
        to_merge_reord.sort_values(by=['GROUP_ID','VARIABLE_GROUP','VARIABLE'],ascending=[True, False,True],inplace=True)
        to_merge_reord.to_csv(path_output_merge,index=False)
    
    # recalculate GROUP_ID
    cnt_grp_id = 0
    cnt_f = 1
    for K_args in [path_output_varinfo_hh, path_output_varinfo_dd, path_output_varinfo_ww, path_output_varinfo_mm, path_output_varinfo_yy, path_output_merge]:
        df_1 = load_csv(K_args)
        log.info('file [%d]: %s; min(GROUP_ID): %d; max(GROUP_ID): %d' % (cnt_f, K_args, df_1['GROUP_ID'].min(), df_1['GROUP_ID'].max()))
        if cnt_f == 1:
            log.info('for file 1 the GROUP_IDs are not recalculated')
        else:
            df_1['GROUP_ID'] = df_1['GROUP_ID'] + cnt_grp_id
            log.info('[RECALCULATED GROUP_ID] file [%d]: %s; min(GROUP_ID): %d; max(GROUP_ID): %d' % (cnt_f, K_args, df_1['GROUP_ID'].min(), df_1['GROUP_ID'].max()))
        # for each group VAR_INFO_VARNAME must be the first
        df_1['VAR_INFO_VARNAME_ID'] = 0
        df_1.loc[(df_1['VARIABLE'] == 'VAR_INFO_VARNAME'),'VAR_INFO_VARNAME_ID'] = 1
        df_1.sort_values(by=['GROUP_ID','VARIABLE_GROUP','VAR_INFO_VARNAME_ID','VARIABLE'],ascending=[True, False, False,True],inplace=True)
        df_1.drop(columns=['VAR_INFO_VARNAME_ID'],inplace=True)
        df_1.to_csv(K_args, index=False)
        cnt_grp_id = df_1['GROUP_ID'].max()
        cnt_f = cnt_f + 1
