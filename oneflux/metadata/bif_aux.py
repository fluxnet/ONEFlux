'''
oneflux.metadata.bif

For license information:
see LICENSE file or headers in oneflux.__init__.py 

AUX files BIF metadata handling functions for ONEFlux

@author: Carlo Trotta
@contact: trottacarlo@unitus.it
@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2025-10-30
'''

import os
import pandas as pd
import numpy
import argparse
import datetime
import logging

from oneflux.metadata.bif_var_info import dict2ONEFluxPipelineLog
from oneflux.pipeline.common import MODE_ISSUER, MODE_PROCENTER
from oneflux import VERSION

log = logging.getLogger(__name__)

GRP_ERA_DOWN = ['ERA_SLOPE','ERA_INTERCEPT','ERA_RMSE','ERA_CORRELATION']
GRP_UST_THR = ['USTAR_MP_METHOD','USTAR_CP_METHOD']

def recalculateIDs(df):
    df['IDnew'] = numpy.NaN
    cntID = 0
    # IDs change for each line
    for xx_method in['USTAR_MP_METHOD','USTAR_CP_METHOD','NEE_CUT_USTAR50','NEE_VUT_USTAR50']:
        suby_USTAR_XX_METHOD = df.loc[(df['VARIABLE'] == xx_method)]
        if suby_USTAR_XX_METHOD.shape[0] == 0:
            continue
        for idx2 in suby_USTAR_XX_METHOD.index:
            cntID = cntID + 1
            df.loc[idx2,'IDnew'] = cntID
    while sum(pd.isnull(df['IDnew'])) > 0:
        first_NA = df.index[(pd.isnull(df['IDnew']) == 1)][0]
        cntID = cntID + 1
        df.loc[(
            (df['VARIABLE'] == df.loc[first_NA,'VARIABLE']) &
            (df['ID'] == df.loc[first_NA,'ID']) &
            (df['TIMESTAMP'] == df.loc[first_NA,'TIMESTAMP'])),'IDnew'] = cntID
    #df.to_csv('df_IDnew.csv',index=False)
    df.drop( columns = ['ID'],inplace=True)
    df.rename(columns = {'IDnew': 'ID'},inplace=True)
    
    return df

def run_bif_aux(zipfilename, input_path_aux_meteo=None, input_path_aux_nee=None, file_output_path=None, path_file_pipeline=None):
    
    file_list = [input_path_aux_meteo,input_path_aux_nee]
    """for root_d,dir_d,file_d in os.walk(input_path):
        for ff in file_d:
            if (('_AUXMETEO_' in ff)or('_AUXNEE_' in ff)):
                file_list.append( os.path.join(root_d,ff) )"""
    log.info('file *_AUXMETEO_*: %s' % (input_path_aux_meteo))
    log.info('file *_AUXNEE_*: %s' % (input_path_aux_nee))
    """    ID,VARIABLE,PARAMETER,VALUE,TIMESTAMP
    1,TA,ERA_SLOPE,1.01,-9999
    1,TA,ERA_INTERCEPT,-0.16,-9999
    1,TA,ERA_RMSE,9.01,-9999
    1,TA,ERA_CORRELATION,0.65,-9999"""
    BIF = {'SITE_ID': [], 'GROUP_ID': [], 'VARIABLE_GROUP': [], 'VARIABLE': [], 'DATAVALUE': []}
    # get informations from ONEFlux_pipeline_*.log as dictionary
    pipeline_infos = dict2ONEFluxPipelineLog(path_file_pipeline)
    
    cnt_grp = 0
    for ff in file_list:
        log.info('open file: %s' % ff)
        # FLX_BE-Lon_FLUXNET2015_AUXMETEO_2018-2018_beta-3.csv
        sitecode = os.path.basename(ff).split('_')[1]
        df = pd.read_csv(ff)
        # in the AUXNEE IDs mut be recalculated
        if ff == input_path_aux_nee:
            df = recalculateIDs(df)
        for id_u in df['ID'].unique():
            sub_g = df.loc[(df['ID'] == id_u)]
            if cnt_grp == 0: # FILL GRP_ONEFLUX
                cnt_grp = cnt_grp + 1
                BIF['SITE_ID'].append(pipeline_infos['sitecode'])
                BIF['GROUP_ID'].append(cnt_grp)
                BIF['VARIABLE_GROUP'].append('GRP_ONEFLUX')
                BIF['VARIABLE'].append('PRODUCT_SOURCE_NETWORK')
                BIF['DATAVALUE'].append(MODE_ISSUER) # Valid entries: AMF, ASF, CNF, JPF, KOF, MXF, NEON, ICOS, EUF, OZF, TERN, SAEON, FLX

                BIF['SITE_ID'].append(pipeline_infos['sitecode'])
                BIF['GROUP_ID'].append(cnt_grp)
                BIF['VARIABLE_GROUP'].append('GRP_ONEFLUX')
                BIF['VARIABLE'].append('PRODUCT_FIRST_YEAR')
                BIF['DATAVALUE'].append(pipeline_infos['first_year'])

                BIF['SITE_ID'].append(pipeline_infos['sitecode'])
                BIF['GROUP_ID'].append(cnt_grp)
                BIF['VARIABLE_GROUP'].append('GRP_ONEFLUX')
                BIF['VARIABLE'].append('PRODUCT_LAST_YEAR')
                BIF['DATAVALUE'].append(pipeline_infos['last_year'])

                BIF['SITE_ID'].append(pipeline_infos['sitecode'])
                BIF['GROUP_ID'].append(cnt_grp)
                BIF['VARIABLE_GROUP'].append('GRP_ONEFLUX')
                BIF['VARIABLE'].append('PRODUCT_TIME_RESOLUTION')
                BIF['DATAVALUE'].append(pipeline_infos['record_interval'].upper())

                BIF['SITE_ID'].append(pipeline_infos['sitecode'])
                BIF['GROUP_ID'].append(cnt_grp)
                BIF['VARIABLE_GROUP'].append('GRP_ONEFLUX')
                BIF['VARIABLE'].append('PRODUCT_NAME')
                BIF['DATAVALUE'].append(zipfilename)

                BIF['SITE_ID'].append(pipeline_infos['sitecode'])
                BIF['GROUP_ID'].append(cnt_grp)
                BIF['VARIABLE_GROUP'].append('GRP_ONEFLUX')
                BIF['VARIABLE'].append('PRODUCT_ONEFLUX_VERSION')
                BIF['DATAVALUE'].append(VERSION) # FULL VERSION OF ONEFLUX

                BIF['SITE_ID'].append(pipeline_infos['sitecode'])
                BIF['GROUP_ID'].append(cnt_grp)
                BIF['VARIABLE_GROUP'].append('GRP_ONEFLUX')
                BIF['VARIABLE'].append('PRODUCT_PROCESSING_CENTER')
                BIF['DATAVALUE'].append(MODE_PROCENTER) # Valid entries: EUDB_ICOS, AMP, TERN

                BIF['SITE_ID'].append(pipeline_infos['sitecode'])
                BIF['GROUP_ID'].append(cnt_grp)
                BIF['VARIABLE_GROUP'].append('GRP_ONEFLUX')
                BIF['VARIABLE'].append('PRODUCT_PROCESSING_DATE')
                PRODUCT_PROCESSING_DATE = datetime.datetime.now()
                PRODUCT_PROCESSING_DATE = '%04d%02d%02d' % (PRODUCT_PROCESSING_DATE.year,PRODUCT_PROCESSING_DATE.month,PRODUCT_PROCESSING_DATE.day)
                BIF['DATAVALUE'].append(PRODUCT_PROCESSING_DATE)
                
                # BIF['SITE_ID'].append(pipeline_infos['sitecode'])
                # BIF['GROUP_ID'].append(cnt_grp)
                # BIF['VARIABLE_GROUP'].append('GRP_ONEFLUX')
                # BIF['VARIABLE'].append('PRODUCT_RELEASE_NUMBER')
                # BIF['DATAVALUE'].append('TODO')

                # BIF['SITE_ID'].append(pipeline_infos['sitecode'])
                # BIF['GROUP_ID'].append(cnt_grp)
                # BIF['VARIABLE_GROUP'].append('GRP_ONEFLUX')
                # BIF['VARIABLE'].append('PRODUCT_RELEASE_NOTE')
                # BIF['DATAVALUE'].append('TODO')

                # BIF['SITE_ID'].append(pipeline_infos['sitecode'])
                # BIF['GROUP_ID'].append(cnt_grp)
                # BIF['VARIABLE_GROUP'].append('GRP_ONEFLUX')
                # BIF['VARIABLE'].append('PRODUCT_RELEASE_VARS_AFFECTED')
                # BIF['DATAVALUE'].append('TODO')

                # BIF['SITE_ID'].append(pipeline_infos['sitecode'])
                # BIF['GROUP_ID'].append(cnt_grp)
                # BIF['VARIABLE_GROUP'].append('GRP_ONEFLUX')
                # BIF['VARIABLE'].append('PRODUCT_DOWNLOAD_LINK')
                # BIF['DATAVALUE'].append('TODO')

            #end if cnt_grp == 0: # FILL GRP_ONEFLUX
            cnt_grp = cnt_grp + 1
            for mth in ['CP','MP']:
                if sum(sub_g['VARIABLE'] == 'USTAR_%s_METHOD' % mth) > 0:
                    """
                    ID    VARIABLE    PARAMETER    VALUE    TIMESTAMP
                    1    USTAR_MP_METHOD    SUCCESS_RUN    1    2018
                    2    USTAR_CP_METHOD    SUCCESS_RUN    0    2018
                    """
                    BIF['SITE_ID'].append(sitecode)
                    BIF['GROUP_ID'].append(cnt_grp)
                    BIF['VARIABLE_GROUP'].append('GRP_UST_THR')
                    BIF['VARIABLE'].append(sub_g.loc[sub_g.index[0],'VARIABLE'].replace('_METHOD','_SUCCESS_RUN'))
                    BIF['DATAVALUE'].append(sub_g.loc[sub_g.index[0],'VALUE'])
                    # YEAR
                    BIF['SITE_ID'].append(sitecode)
                    BIF['GROUP_ID'].append(cnt_grp)
                    BIF['VARIABLE_GROUP'].append('GRP_UST_THR')
                    BIF['VARIABLE'].append(sub_g.loc[sub_g.index[0],'VARIABLE'].replace('_METHOD','_SUCCESS_RUN_YEAR'))
                    BIF['DATAVALUE'].append(sub_g.loc[sub_g.index[0],'TIMESTAMP'])
            # end for mth in ['CP','MP']:
            for mth in ['CUT','VUT']:
                if sum(sub_g['VARIABLE'] == 'USTAR_%s' % mth) > 0:
                    BIF['SITE_ID'].append(sitecode)
                    BIF['GROUP_ID'].append(cnt_grp)
                    BIF['VARIABLE_GROUP'].append('GRP_UST_THR')
                    BIF['VARIABLE'].append('USTAR_VERSION')
                    BIF['DATAVALUE'].append(mth)
                    
                    BIF['SITE_ID'].append(sitecode)
                    BIF['GROUP_ID'].append(cnt_grp)
                    BIF['VARIABLE_GROUP'].append('GRP_UST_THR')
                    BIF['VARIABLE'].append('USTAR_THRESHOLD')
                    BIF['DATAVALUE'].append(sub_g.loc[(sub_g['PARAMETER'] == 'USTAR_THRESHOLD'),'VALUE'].values[0])
                    
                    BIF['SITE_ID'].append(sitecode)
                    BIF['GROUP_ID'].append(cnt_grp)
                    BIF['VARIABLE_GROUP'].append('GRP_UST_THR')
                    BIF['VARIABLE'].append('USTAR_PERCENTILE')
                    BIF['DATAVALUE'].append(sub_g.loc[(sub_g['PARAMETER'] == 'USTAR_PERCENTILE'),'VALUE'].values[0])
                    if mth == 'VUT':
                        BIF['SITE_ID'].append(sitecode)
                        BIF['GROUP_ID'].append(cnt_grp)
                        BIF['VARIABLE_GROUP'].append('GRP_UST_THR')
                        BIF['VARIABLE'].append('USTAR_PERCENTILE_YEAR')
                        BIF['DATAVALUE'].append(sub_g.loc[(sub_g['PARAMETER'] == 'USTAR_PERCENTILE'),'TIMESTAMP'].values[0])
            #end for mth in ['CUT','VUT']:
            for flx_opt in ['NEE', 'RECO_NT', 'RECO_DT', 'GPP_NT', 'GPP_DT']:
                for flx_opt2 in ['CUT', 'VUT']:
                    v_name = '%s_%s_REF' % (flx_opt,flx_opt2)
                    if sum(sub_g['VARIABLE'] == v_name) > 0:
                        """
                        ID    VARIABLE    PARAMETER    VALUE    TIMESTAMP
                        5    NEE_CUT_REF    HH_USTAR_PERCENTILE    -9999    -9999
                        5    NEE_CUT_REF    HH_USTAR_THRESHOLD    -9999    -9999
                        6    NEE_VUT_REF    HH_USTAR_PERCENTILE    41.25    2018
                        6    NEE_VUT_REF    HH_USTAR_THRESHOLD    0.153614    2018
                        """
                        BIF['SITE_ID'].append(sitecode)
                        BIF['GROUP_ID'].append(cnt_grp)
                        BIF['VARIABLE_GROUP'].append('GRP_FLUX_REF')
                        BIF['VARIABLE'].append('REF_VARIABLE')
                        BIF['DATAVALUE'].append(flx_opt)

                        BIF['SITE_ID'].append(sitecode)
                        BIF['GROUP_ID'].append(cnt_grp)
                        BIF['VARIABLE_GROUP'].append('GRP_FLUX_REF')
                        BIF['VARIABLE'].append('REF_VERSION')
                        BIF['DATAVALUE'].append(flx_opt2)
                
                        BIF['SITE_ID'].append(sitecode)
                        BIF['GROUP_ID'].append(cnt_grp)
                        BIF['VARIABLE_GROUP'].append('GRP_FLUX_REF')
                        BIF['VARIABLE'].append('REF_TIME_RESOLUTION')
                        for opt_perc in ['HH', 'DD', 'WW', 'MM', 'YY']:
                            if sum(sub_g['PARAMETER'] == '%s_USTAR_PERCENTILE' % opt_perc) > 0:
                                BIF['DATAVALUE'].append(opt_perc)
                                break

                        BIF['SITE_ID'].append(sitecode)
                        BIF['GROUP_ID'].append(cnt_grp)
                        BIF['VARIABLE_GROUP'].append('GRP_FLUX_REF')
                        BIF['VARIABLE'].append('REF_USTAR_THRESHOLD')
                        for opt_perc in ['HH', 'DD', 'WW', 'MM', 'YY']:
                            if sum(sub_g['PARAMETER'] == '%s_USTAR_THRESHOLD' % opt_perc) > 0:
                                BIF['DATAVALUE'].append(
                                    sub_g.loc[(sub_g['PARAMETER'] == '%s_USTAR_THRESHOLD' % opt_perc),'VALUE'].values[0]
                                )
                                break

                        BIF['SITE_ID'].append(sitecode)
                        BIF['GROUP_ID'].append(cnt_grp)
                        BIF['VARIABLE_GROUP'].append('GRP_FLUX_REF')
                        BIF['VARIABLE'].append('REF_USTAR_PERCENTILE')
                        for opt_perc in ['HH', 'DD', 'WW', 'MM', 'YY']:
                            if sum(sub_g['PARAMETER'] == '%s_USTAR_PERCENTILE' % opt_perc) > 0:
                                BIF['DATAVALUE'].append(
                                    sub_g.loc[(sub_g['PARAMETER'] == '%s_USTAR_PERCENTILE' % opt_perc),'VALUE'].values[0]
                                )
                                break
                        if flx_opt2 == 'VUT':
                            BIF['SITE_ID'].append(sitecode)
                            BIF['GROUP_ID'].append(cnt_grp)
                            BIF['VARIABLE_GROUP'].append('GRP_FLUX_REF')
                            BIF['VARIABLE'].append('REF_YEAR')
                            for opt_perc in ['HH', 'DD', 'WW', 'MM', 'YY']:
                                if sum(sub_g['PARAMETER'] == '%s_USTAR_THRESHOLD' % opt_perc) > 0:
                                    BIF['DATAVALUE'].append(
                                        sub_g.loc[(sub_g['PARAMETER'] == '%s_USTAR_THRESHOLD' % opt_perc),'TIMESTAMP'].values[0]
                                    )
                                    break
                # end for flx_opt2 in ['CUT', 'VUT']:
            #end for flx_opt in ['NEE', 'RECO_NT', 'RECO_DT', 'GPP_NT', 'GPP_DT']:
            if sum(sub_g['PARAMETER'] == 'ERA_SLOPE')>0:
                """
                ID    VARIABLE    PARAMETER    VALUE    TIMESTAMP
                1    TA    ERA_SLOPE    1.01    -9999
                1    TA    ERA_INTERCEPT    -0.16    -9999
                1    TA    ERA_RMSE    9.01    -9999
                1    TA    ERA_CORRELATION    0.65    -9999
                """
                for era_v in ['ERA_SLOPE','ERA_INTERCEPT','ERA_RMSE','ERA_CORRELATION']:
                    BIF['SITE_ID'].append(sitecode)
                    BIF['GROUP_ID'].append(cnt_grp)
                    BIF['VARIABLE_GROUP'].append('GRP_ERA_DOWN')
                    BIF['VARIABLE'].append(era_v)
                    BIF['DATAVALUE'].append(
                        sub_g.loc[(sub_g['PARAMETER'] == era_v),'VALUE'].values[0]
                    )
                BIF['SITE_ID'].append(sitecode)
                BIF['GROUP_ID'].append(cnt_grp)
                BIF['VARIABLE_GROUP'].append('GRP_ERA_DOWN')
                BIF['VARIABLE'].append('ERA_VARIABLE')
                BIF['DATAVALUE'].append(
                    sub_g.loc[sub_g.index[0],'VARIABLE']
                )
                
    BIF = pd.DataFrame.from_dict(BIF)
    BIF = BIF[['SITE_ID','GROUP_ID','VARIABLE_GROUP','VARIABLE','DATAVALUE']]

    if not os.path.exists(os.path.dirname(file_output_path)):
        os.makedirs(os.path.dirname(file_output_path), exist_ok=True)
    BIF.to_csv(file_output_path,index=False)
    log.info('write file: %s' % file_output_path)
