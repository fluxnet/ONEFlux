'''
oneflux.metadata.bif_var_info

For license information:
see LICENSE file or headers in oneflux.__init__.py 

Variable information BIF metadata handling functions for ONEFlux

@author: Carlo Trotta
@contact: trottacarlo@unitus.it
@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2025-10-30
'''
import os
import argparse
import pandas as pd
import numpy
import datetime
import logging
import sys

log = logging.getLogger(__name__)

SPECIAL_CASE_VAR_NAME = "FIRST"

def addFirstVarInfo(v_nameL,firstValid,df_varinfo):
    # add fake varinfo variable if missing
    log.info('[CHECK MISSING VARIABLE in VARINFO] check variables found in DATA but missing in VARINFO')
    if not isinstance(v_nameL,list):
        v_nameL = [v_nameL]
    to_add = []
    for v_name in v_nameL:
        if sum(df_varinfo['DATAVALUE'] == v_name) == 0:
            if not SPECIAL_CASE_VAR_NAME == v_name:
                log.info('[CHECK MISSING VARIABLE in VARINFO] %s variable found in DATA but missing in VARINFO' % (v_name))
            group_ids = df_varinfo['GROUP_ID'].copy().astype(int)
            new_grp = max(group_ids)
            while (1):
                if sum(group_ids == new_grp) == 0:
                    break
                new_grp = new_grp + 1
            log.warning('variable: %s added to VAR_INFO with GROUP_ID: %s' % (v_name,new_grp))
            df_varinfo1 = pd.concat([
                pd.DataFrame.from_dict({
                    'SITE_ID': [df_varinfo.loc[(df_varinfo.index[0]),'SITE_ID']],
                    'GROUP_ID': ['%d' % new_grp],
                    'VARIABLE_GROUP': [df_varinfo.loc[(df_varinfo.index[0]),'VARIABLE_GROUP']],
                    'VARIABLE': ['VAR_INFO_VARNAME'],
                    'DATAVALUE': [v_name]}),
                pd.DataFrame.from_dict({
                    'SITE_ID': [df_varinfo.loc[(df_varinfo.index[0]),'SITE_ID']],
                    'GROUP_ID': ['%d' % new_grp],
                    'VARIABLE_GROUP': [df_varinfo.loc[(df_varinfo.index[0]),'VARIABLE_GROUP']],
                    'VARIABLE': ['VAR_INFO_DATE'],
                    'DATAVALUE': [firstValid.loc[(firstValid['variable'] ==SPECIAL_CASE_VAR_NAME),'TIMESTAMP_START'].values[0]]})
            ],ignore_index=True)
            df_varinfo = pd.concat([df_varinfo,df_varinfo1],ignore_index=True)
            to_add.append(df_varinfo1)
    
    log.info('[CHECK MISSING VARIABLE in VARINFO] check variables found in DATA but missing in VARINFO ...completed')

    return df_varinfo,to_add
    
def checkMultipleGROUP_ID(df):
    #TO CHECK
    uni_grp = df['GROUP_ID'].unique().tolist()
    
    while len(uni_grp) > 0: 
        suby = df.loc[(df['GROUP_ID'] == uni_grp[0])]
        vname = suby.loc[(suby['VARIABLE'] == 'VAR_INFO_VARNAME'),'DATAVALUE'].unique().tolist()
        if len(vname) == 1:
            uni_grp.pop(0)
            continue
        log.warning('GROUP_ID: %d with %d VAR_INFO_VARNAME (%s)' % ( idx,
            len(vname),
            '; '.join(vname))
        )
        new_id = max(uni_grp) + 1
        while new_id in uni_grp:
            new_id = max(uni_grp) + 1
        log.warning('VAR_INFO_VARNAME: %s; GROUP_ID: %d replaced as %d' % ( vname[0],new_id))
        df.loc[(
            (df['VAR_INFO_VARNAME'] == vname[0]) &
            (df['GROUP_ID'] == uni_grp[0])),'GROUP_ID'] = new_id
        raise
    return df
    
def fixLengthDate(date_or):
    """ add date are fixed as YYYYMMDDHHMN (column: 'TIMESTAMP_fix')"""
    if isinstance(date_or,str):
        TIMESTAMP_fix = int(date_or)
    else:
        TIMESTAMP_fix = date_or.copy()
    str_fix = 'YYYYMMDDHHMN'
    #log.info('original value: %d' % TIMESTAMP_fix)
    if len('%d' % TIMESTAMP_fix) == len('YYYY'):
        #log.info('add month: 1')
        TIMESTAMP_fix = TIMESTAMP_fix * (10**2)
        TIMESTAMP_fix = TIMESTAMP_fix + 1
    if len('%d' % TIMESTAMP_fix) == len('YYYYMM'):
        #log.info('add day: 1')
        TIMESTAMP_fix = TIMESTAMP_fix * (10**2)
        TIMESTAMP_fix = TIMESTAMP_fix + 1
    if len('%d' % TIMESTAMP_fix) == len('YYYYMMDD'):
        #log.info('add hour: 0')
        TIMESTAMP_fix = TIMESTAMP_fix * (10**2)
    if len('%d' % TIMESTAMP_fix) == len('YYYYMMDDHH'):
        #log.info('add minute: 0')
        TIMESTAMP_fix = TIMESTAMP_fix * (10**2)
    #log.info('fixed value:    %d' % TIMESTAMP_fix)
    if isinstance(date_or,str):
        TIMESTAMP_fix = str(TIMESTAMP_fix)
    
    return TIMESTAMP_fix


def getFirstValidFrom00fp(dir_00_fp):
    
    dict_02 = {}
    for root02,dir02,file02 in os.walk(dir_00_fp):
        for ff in file02:
            if '_qcv_' in ff:
                log.info('open file: %s' % os.path.join(root02,ff))
                nr_h = 0
                with open(os.path.join(root02,ff)) as fn:
                    for line in fn.readlines():
                        if line.startswith('TIMESTAMP_START'):
                            break
                        nr_h = nr_h + 1
                df = pd.read_csv(os.path.join(root02,ff),skiprows = nr_h)
                df['file'] = ff
                if '_qcv_' in ff:
                    df['des_file'] = '_qcv_'
                """if '_qca_energy_' in ff:
                    df['des_file'] = '_qca_energy_'
                if '_qca_meteo_' in ff:
                    df['des_file'] = '_qca_meteo_'
                if '_qca_nee_' in ff:
                    df['des_file'] = '_qca_nee_'
                """
                for col in df.columns:
                    if col.startswith('TIMESTAMP'):
                        continue
                    if col =='file':
                        continue
                    if col =='des_file':
                        continue
                    df.loc[(df[col] < -9990),col] = numpy.NaN
                    if not col in dict_02.keys():
                        dict_02[col] = []
                    dict_02[col].append(df[['TIMESTAMP_START',col]])#,'file','des_file'
                    if col == 'NEE':
                        for col_1 in ['FC','SC']:
                            log.info('duplicates NEE info as %s' % col_1)
                            if not col_1 in dict_02.keys():
                                dict_02[col_1] = []
                            dict_02[col_1].append(df[['TIMESTAMP_START',col]])#,'file','des_file'
                        
    # concat years and get first valid value
    firstValid = {'variable': [], 'TIMESTAMP_START': []}
    data_ts = []
    for k1,v1 in dict_02.items():
        log.info('merge datasets of the variable: %s' % k1)
        v1 = pd.concat(v1,ignore_index=True)
        v1.sort_values(by = ['TIMESTAMP_START'],inplace=True)
        data_ts = data_ts + v1['TIMESTAMP_START'].to_list()
        if len(firstValid['variable']) == 0:
            # add date of SPECIAL_CASE_VAR_NAME
            firstValid['variable'].append(SPECIAL_CASE_VAR_NAME)
            firstValid['TIMESTAMP_START'].append(v1.loc[v1.index[0],'TIMESTAMP_START'])
            
        v1.dropna(inplace=True)
        v1.drop_duplicates(inplace=True)
        v1.sort_values(by = ['TIMESTAMP_START'],inplace=True)
        v1.reset_index(inplace=True,drop=True)
        firstValid['variable'].append(k1)
        firstValid['TIMESTAMP_START'].append(v1.loc[v1.index[0],'TIMESTAMP_START'])
    
    firstValid = pd.DataFrame.from_dict(firstValid)
    data_ts = pd.DataFrame.from_dict({'TIMESTAMP_START': data_ts})

    data_ts.drop_duplicates(inplace=True)
    data_ts.sort_values(by = ['TIMESTAMP_START'],ascending=True,inplace=True)
    data_ts.reset_index(inplace=True,drop=True)
    for idx in firstValid.index:
        if firstValid.loc[idx,'variable'] == SPECIAL_CASE_VAR_NAME:
            continue
        log.info('variable: %s; first %s: %d' % (
            firstValid.loc[idx,'variable'],
            'TIMESTAMP_START',
            firstValid.loc[idx,'TIMESTAMP_START']
        ))
    return firstValid,data_ts

def fillVarInfoDate(df_varinfo,firstValid):
    to_add = []
    missing_variable = []    
    for grp_id in df_varinfo['GROUP_ID'].unique():
        grp_x = df_varinfo.loc[(df_varinfo['GROUP_ID'] == grp_id)]
        v_x = grp_x.loc[(grp_x['VARIABLE'] == 'VAR_INFO_VARNAME'),'DATAVALUE'].values[0]
        if sum(firstValid['variable'] == v_x) == 0:
            log.error('[FILL VAR_INFO_DATE] variable %s is missing in dataset but found in VAR_INFO' % v_x)
            continue
        if sum(grp_x['VARIABLE'] == 'VAR_INFO_DATE') == 0:
            date_1 = firstValid.loc[
                (firstValid['variable'] == v_x),'TIMESTAMP_START'].values[0]
            grp_fill = pd.DataFrame.from_dict({
                'SITE_ID': [grp_x.loc[(grp_x.index[0]),'SITE_ID']],
                'GROUP_ID': [grp_x.loc[(grp_x.index[0]),'GROUP_ID']],
                'VARIABLE_GROUP': [grp_x.loc[(grp_x.index[0]),'VARIABLE_GROUP']],
                'VARIABLE': ['VAR_INFO_DATE'],
                'DATAVALUE': [date_1]
            })
            log.warning('[FILL VAR_INFO_DATE] GROUP_ID: %d; VAR_INFO_NAME: %s; missing VAR_INFO_DATE, filled with %s' % (grp_id,
                grp_x.loc[(grp_x['VARIABLE'] == 'VAR_INFO_VARNAME'),'DATAVALUE'].values[0],date_1))
            to_add.append(grp_fill)
    log.info('[FILL VAR_INFO_DATE] dataset %d row%s' % (df_varinfo.shape[0],'s' if df_varinfo.shape[0] > 1 else ''))
    log.info('[FILL VAR_INFO_DATE] %d VAR_INFO_DATE%s added to the VAR_INFO dataset' % (len(to_add),'s' if len(to_add) > 1 else ''))
    if len(to_add) > 0:
        to_add = pd.concat(to_add,ignore_index=True)
        to_add['DATAVALUE'] = to_add['DATAVALUE'].astype(str)
        
        df_varinfo = pd.concat([df_varinfo,to_add],ignore_index=True)
        df_varinfo.sort_values(by=['GROUP_ID'],inplace=True)
        df_varinfo.reset_index(inplace=True,drop=True)

    log.info('[FILL VAR_INFO_DATE] dataset %d row%s' % (df_varinfo.shape[0],'s' if df_varinfo.shape[0] > 1 else ''))

    return df_varinfo
    
def removeDuplicatesInGROUP_ID(df_varinfo):
    """different GROUP_ID but same informations"""
    grp_id_u = df_varinfo['GROUP_ID'].unique()
    log.info('[CHECK REPLICATES VARIABLE IN GROUP] dataset %d row%s' % (df_varinfo.shape[0],'s' if df_varinfo.shape[0] > 1 else ''))
    for g in grp_id_u:
        suby = df_varinfo.loc[(df_varinfo['GROUP_ID'] == g),].copy()
        if len(suby['VARIABLE'].unique()) < suby.shape[0]:
            for vu in suby['VARIABLE'].unique():
                if sum(suby['VARIABLE'] == vu) == 1:
                    continue
                log.warning('[CHECK REPLICATES VARIABLE IN GROUP] GROUP_ID: %d; %d rows with VARIABLE == %s (these lines are removed from the dataset)' % (g,
                    sum(suby['VARIABLE'] == vu),vu))
                for idx in suby.index:
                    if suby.loc[idx,'VARIABLE'] == vu:
                        df_varinfo.drop(idx,inplace=True)
    log.info('[CHECK REPLICATES VARIABLE IN GROUP] dataset %d row%s' % (df_varinfo.shape[0],'s' if df_varinfo.shape[0] > 1 else ''))
    return df_varinfo

def checkVarnameVarHeight(df_varinfo):
    """stessa variabile e stessa data ma diversa altezza non e possibile"""
    grp_id = df_varinfo.loc[(df_varinfo['VARIABLE'] == 'VAR_INFO_HEIGHT'),'GROUP_ID']
    merge_grp = []
    for g in grp_id:
        suby = df_varinfo.loc[(df_varinfo['GROUP_ID'] == g),]
        idct_v = {}
        idct_v['id_g'] = [g]
        idct_v['vn'] = suby.loc[(suby['VARIABLE'] == 'VAR_INFO_VARNAME'),'DATAVALUE'].values
        idct_v['vh'] = suby.loc[(suby['VARIABLE'] == 'VAR_INFO_HEIGHT'),'DATAVALUE'].values
        if sum((suby['VARIABLE'] == 'VAR_INFO_DATE')) > 0:
            idct_v['vd'] = suby.loc[(suby['VARIABLE'] == 'VAR_INFO_DATE'),'DATAVALUE'].values
        else:
            idct_v['vd'] = [numpy.NaN]
        merge_grp.append(pd.DataFrame.from_dict(idct_v))
    merge_grp = pd.concat(merge_grp,ignore_index=True)
    no_replicates = []
    while merge_grp.shape[0] > 0:
        ref = merge_grp.loc[merge_grp.index[0]]
        no_replicates.append(ref)
        merge_grp.drop(merge_grp.index[0],inplace=True)
        if pd.isnull(ref['vd']):
            w = ((merge_grp['vn'] == ref['vn']) &
                (pd.isnull(merge_grp['vd']) == 1))
        else:
            w = ((merge_grp['vn'] == ref['vn']) &
                (merge_grp['vd'] == ref['vd']))
        
        if sum(w) > 0:
            log.info('[CHECK REPLICATES VARNAME+VARDATE no VARHEIGHT] dataset %d row%s' % (df_varinfo.shape[0],'s' if df_varinfo.shape[0] > 1 else ''))
            log.warning('[CHECK REPLICATES VARNAME+VARDATE no VARHEIGHT] [REFERENCE] GROUP_ID: %d and [COMPARISON] GROUP_ID: %s have identical VAR_INFO_VARNAME: %s and VAR_INFO_DATE: %s but different VAR_INFO_HEIGHT: %s' % (
                    ref['id_g'],', '.join([str(xx) for xx in merge_grp.loc[w,'id_g'].values]),ref['vn'],ref['vd'],', '.join([str(xx) for xx in merge_grp.loc[w,'vh'].values]))
            )
            for xx in merge_grp.loc[w,'id_g'].values:
                log.warning('[CHECK REPLICATES VARNAME+VARDATE no VARHEIGHT][COMPARISON] GROUP_ID: %s (%s row%s) REMOVED from the dataset' % (xx,
                    sum(df_varinfo['GROUP_ID'] == xx),'s' if sum(df_varinfo['GROUP_ID'] == xx) > 1 else ''))
                df_varinfo.drop(df_varinfo.index[(df_varinfo['GROUP_ID'] == xx)],inplace = True)
                merge_grp.drop(merge_grp.index[(merge_grp['id_g'] == xx)],inplace = True)
            log.info('[CHECK REPLICATES VARNAME+VARDATE no VARHEIGHT] dataset %d row%s' % (df_varinfo.shape[0],'s' if df_varinfo.shape[0] > 1 else ''))

    return df_varinfo

def removeReplicatesGRPvarinfo(df_to_check=None):
    
    msg_1 = '[CHECK DUPLICATES GROUP WITH SAME VAR_INFO_VARNAME] dataset %d row%s' % (df_to_check.shape[0],'s' if df_to_check.shape[0] > 1 else '')
    log.info(msg_1)
        
    vname_list = df_to_check.loc[(df_to_check['VARIABLE'] == 'VAR_INFO_VARNAME'),'DATAVALUE'].unique().tolist()
    for vname in vname_list:
        grp_id_v = df_to_check.loc[(df_to_check['DATAVALUE'] == vname),'GROUP_ID'].unique().tolist()
        if len(grp_id_v) == 1:
            continue
        msg_1 = '[CHECK DUPLICATES GROUP WITH SAME VAR_INFO_VARNAME] check duplicates group with VAR_INFO_VARNAME %s (%d group%s)' % (vname,len(grp_id_v),'s' if len(grp_id_v) > 1 else '')
        log.info(msg_1)
            
        for grp_id_ref in grp_id_v:
            if sum(df_to_check['GROUP_ID'] == grp_id_ref) == 0:
                continue
            for grp_id_cmp in grp_id_v:
                if grp_id_ref == grp_id_cmp:
                    continue
                if sum(df_to_check['GROUP_ID'] == grp_id_cmp) == 0:
                    continue
                grp_ref = df_to_check.loc[(df_to_check['GROUP_ID'] == grp_id_ref)].copy()
                grp_cmp = df_to_check.loc[(df_to_check['GROUP_ID'] == grp_id_cmp)].copy()
                msg_1 = '[CHECK DUPLICATES GROUP WITH SAME VAR_INFO_VARNAME] VAR_INFO_VARNAME %s; compare GROUP_ID (reference): %d (%d row%s) and in GROUP_ID (comparison): %d (%d row%s)' % (
                            vname,
                            grp_id_ref,grp_ref.shape[0],'s' if grp_ref.shape[0] > 1 else '',
                            grp_id_cmp,grp_cmp.shape[0],'s' if grp_cmp.shape[0] > 1 else '')
                log.info(msg_1)
                    
                grp_ref.set_index('VARIABLE',inplace=True)
                grp_cmp.set_index('VARIABLE',inplace=True)
                grp_ref = grp_ref.add_suffix('__ref')
                grp_cmp = grp_cmp.add_suffix('__cmp')

                subset_merge = pd.concat([grp_ref,grp_cmp],axis=1,ignore_index=False)

                # compare eache column
                isDiff = 0
                for idx in subset_merge.index:
                    for col in df_to_check.columns:
                        if ((col == 'GROUP_ID')or(col == 'SITE_ID')or(col == 'VARIABLE')or(col == 'VARIABLE_GROUP')):
                            continue
                        if subset_merge.loc[idx,'%s__ref' % col] == subset_merge.loc[idx,'%s__cmp' % col]:
                            continue
                        isDiff = 1
                        
                        msg_1 = '[CHECK DUPLICATES GROUP WITH SAME VAR_INFO_VARNAME] VAR_INFO_VARNAME: %s; VARIABLE: %s; %s are different; "%s" in GROUP_ID %d (reference) and "%s" in GROUP_ID %d (comparison)' % (
                            vname,idx,col,
                            subset_merge.loc[idx,'%s__ref' % col],grp_id_ref,
                            subset_merge.loc[idx,'%s__cmp' % col],grp_id_cmp)
                        log.info(msg_1)
                        break
                    if isDiff == 1:
                        break
                if isDiff == 0:
                    msg_1 = '[CHECK DUPLICATES GROUP WITH SAME VAR_INFO_VARNAME] VAR_INFO_VARNAME %s; %s in GROUP_ID (reference): %d and in GROUP_ID (comparison): %d; are IDENTICAL (%d row%s of the GROUP_ID %d removed from the dataset)' % (
                        vname,col,grp_id_ref,grp_id_cmp,
                        sum(df_to_check['GROUP_ID'] == grp_id_cmp),'s' if sum(df_to_check['GROUP_ID'] == grp_id_cmp) > 1 else '',
                        grp_id_cmp)
                    log.warning(msg_1)
                    df_to_check.drop(df_to_check.index[(df_to_check['GROUP_ID'] == grp_id_cmp)],inplace=True)
                    msg_1 = '[CHECK DUPLICATES GROUP WITH SAME VAR_INFO_VARNAME] dataset %d row%s' % (df_to_check.shape[0],'s' if df_to_check.shape[0] > 1 else '')
                    log.info(msg_1)
    #end for vname in vname_list:
    msg_1 = '[CHECK DUPLICATES GROUP WITH SAME VAR_INFO_VARNAME] dataset %d row%s' % (df_to_check.shape[0],'s' if df_to_check.shape[0] > 1 else '')
    log.info(msg_1)
    return df_to_check
    
def dict2ONEFluxPipelineLog(path_file_pipeline):
    """
    get informations (as dictionary) from command line reported in the file ONEFlux_pipeline_*.log 

    ONEFlux Pipeline: keyword arguments: {
         'nee_partition_nt_execute': True,
         'energy_proc_execute': True,
         'prepare_ure_execute': True,
         'perc_to_compare': ['1.25', '3.75','6.25', '8.75', '11.25', '13.75', '16.25', '18.75', '21.25', '23.75', '26.25', '28.75', '31.25', '33.75', '36.25', '38.75', '41.25',
         '43.75', '46.25', '48.75', '51.25', '53.75', '56.25', '58.75', '61.25', '63.75', '66.25', '68.75', '71.25', '73.75', '76.25', '78.75', '81.25', '83.75', '86.25', '88.75', '91.25', '93.75', '96.25', '98.75', '50'],
         'prod_to_compare': ['c', 'y'],
         'fluxnet2015_version_processing': '5',
         'data_dir':  '/home/c.trotta/RoundRobbin_20251015/AU-ASM',
         'era_first_timestamp_start':  '198101010000',
         'era_source_dir':  '/home/c.trotta/RoundRobbin_20251015/AU-ASM/06_meteo_era__input',
         'meteo_proc_execute': True,
         'tool_dir': '/home/c.trotta/bin/oneflux',
         'ustar_mp_execute': True,
         'fluxnet2015_version_data':  '1',
         'ustar_cp_execute': True,
         'nee_proc_execute': True,
         'ure_execute': True,
         'site_dir':  'AU-ASM',
         'qc_auto_execute': True,
         'fluxnet2015_first_t1': 2010,
         'fluxnet2015_last_t1': 2024,
         'ustar_cp_mcr_dir': '/home/c.trotta/bin/matlab/v94/',
         'fluxnet2015_site_plots': True,
         'data_dir_main':  '/home/c.trotta/RoundRobbin_20251015',
         'record_interval': 'hh',
         'meteo_era_execute': True,
         'era_last_timestamp_start':  '202412312330',
         'simulation': False,
         'first_year': 2010,
         'last_year': 2024,
         'nee_partition_dt_execute': True,
         'fluxnet2015_execute': True}
    """
    pipeline_infos = ''
    with open(path_file_pipeline) as PF:
        for line in PF.readlines():
            # get sitecode
            if 'Using:command (all), ' in line:
                line_s = line.split('site-id ')[1]
                line_s = line_s.split(',')[0]
                line_s = line_s.replace('(','').replace(')','').strip()
            if 'keyword arguments' in line:
                pipeline_infos = line.replace('\n','').replace('\n','')
                break
    pipeline_infos = pipeline_infos.replace(' [oneflux.pipeline.wrappers]','')
    pipeline_infos = pipeline_infos.split('{')[1]
    pipeline_infos = eval('{' + pipeline_infos)
    pipeline_infos['sitecode'] = line_s
    return pipeline_infos


def addGRP_ONEFLUX(pipeline_infos,cnt_grp,BIF):
    
    BIF['SITE_ID'].append(pipeline_infos['sitecode'])
    BIF['GROUP_ID'].append(cnt_grp)
    BIF['VARIABLE_GROUP'].append('GRP_ONEFLUX')
    BIF['VARIABLE'].append('PRODUCT_SOURCE_NETWORK')
    BIF['DATAVALUE'].append('TODO')

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
    BIF['DATAVALUE'].append('TODO')

    BIF['SITE_ID'].append(pipeline_infos['sitecode'])
    BIF['GROUP_ID'].append(cnt_grp)
    BIF['VARIABLE_GROUP'].append('GRP_ONEFLUX')
    BIF['VARIABLE'].append('PRODUCT_ONEFLUX_VERSION')
    BIF['DATAVALUE'].append('TODO')

    BIF['SITE_ID'].append(pipeline_infos['sitecode'])
    BIF['GROUP_ID'].append(cnt_grp)
    BIF['VARIABLE_GROUP'].append('GRP_ONEFLUX')
    BIF['VARIABLE'].append('PRODUCT_PROCESSING_CENTER')
    BIF['DATAVALUE'].append('TODO')

    BIF['SITE_ID'].append(pipeline_infos['sitecode'])
    BIF['GROUP_ID'].append(cnt_grp)
    BIF['VARIABLE_GROUP'].append('GRP_ONEFLUX')
    BIF['VARIABLE'].append('PRODUCT_PROCESSING_DATE')
    PRODUCT_PROCESSING_DATE = datetime.datetime.now()
    PRODUCT_PROCESSING_DATE = '%04d%02d%02d' % (PRODUCT_PROCESSING_DATE.year,PRODUCT_PROCESSING_DATE.month,PRODUCT_PROCESSING_DATE.day)
    BIF['DATAVALUE'].append(PRODUCT_PROCESSING_DATE)
    
    ### 
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
    
    return BIF


def getDefinitionByVariable(v_name,df_definitions):
    df_definitions_1 = df_definitions.loc[(df_definitions['Variable'] == v_name)].copy()

    if df_definitions_1.shape[0] == 0:
        if v_name.startswith('TS_F_MDS_'):
            df_definitions_1 = df_definitions.loc[(df_definitions['Variable'] == 'TS_F_MDS_#')].copy()
        elif v_name.startswith('SWC_F_MDS_'):
            df_definitions_1 = df_definitions.loc[(df_definitions['Variable'] == 'SWC_F_MDS_#')].copy()
        elif v_name.startswith('NEE_CUT_'):
            df_definitions_1 = df_definitions.loc[(df_definitions['Variable'] == 'NEE_CUT_XX')].copy()
        elif v_name.startswith('NEE_VUT_'):
            df_definitions_1 = df_definitions.loc[(df_definitions['Variable'] == 'NEE_VUT_XX')].copy()
        elif v_name.startswith('RECO_NT_CUT_'):
            df_definitions_1 = df_definitions.loc[(df_definitions['Variable'] == 'RECO_NT_CUT_XX')].copy()
        elif v_name.startswith('GPP_NT_CUT_'):
            df_definitions_1 = df_definitions.loc[(df_definitions['Variable'] == 'GPP_NT_CUT_XX')].copy()
        elif v_name.startswith('RECO_NT_VUT_'):
            df_definitions_1 = df_definitions.loc[(df_definitions['Variable'] == 'RECO_NT_VUT_XX')].copy()
        elif v_name.startswith('GPP_NT_VUT_'):
            df_definitions_1 = df_definitions.loc[(df_definitions['Variable'] == 'GPP_NT_VUT_XX')].copy()
        elif v_name.startswith('RECO_DT_CUT_'):
            df_definitions_1 = df_definitions.loc[(df_definitions['Variable'] == 'RECO_DT_CUT_XX')].copy()
        elif v_name.startswith('GPP_DT_CUT_'):
            df_definitions_1 = df_definitions.loc[(df_definitions['Variable'] == 'GPP_DT_CUT_XX')].copy()
        elif v_name.startswith('RECO_DT_VUT_'):
            df_definitions_1 = df_definitions.loc[(df_definitions['Variable'] == 'RECO_DT_VUT_XX')].copy()
        elif v_name.startswith('GPP_DT_VUT_'):
            df_definitions_1 = df_definitions.loc[(df_definitions['Variable'] == 'GPP_DT_VUT_XX')].copy()
    
    return df_definitions_1

def calendarGROUP_ID(data_ts,df_varinfo,firstValid):
    # length of col_timestamp
    col_timestamp = 'TIMESTAMP_START'
    len_date = len('%d' % data_ts.loc[(data_ts.index[0]),col_timestamp])
    df_data_grp_id = data_ts.copy()
    # fill calendar with GROUP_ID
    for vInfo1 in df_varinfo.loc[(df_varinfo['VARIABLE'] == 'VAR_INFO_VARNAME'),'DATAVALUE'].unique():
        grp_idx = df_varinfo.loc[(df_varinfo['DATAVALUE'] ==vInfo1),'GROUP_ID'].values
        grp_date = {'GROUP_ID': [],'VARINFO_DATE': []}
        for idx in grp_idx:
            sub_g = df_varinfo.loc[(df_varinfo['GROUP_ID'] ==idx)].copy()
            grp_date['GROUP_ID'].append(idx)
            if sum(sub_g['VARIABLE'] == 'VAR_INFO_DATE') == 0:
                grp_date['VARINFO_DATE'].append(0)
            else:
                time_v = sub_g.loc[(sub_g['VARIABLE'] == 'VAR_INFO_DATE'),'DATAVALUE'].values[0]
                """
                log.info('time_v: %s' % time_v)
                if len(time_v) == len('YYYY'): # add month
                    time_v = time_v + '01'
                if len(time_v) == len('YYYYMM'):# add day
                    time_v = time_v + '01'
                if len(time_v) == len('YYYYMMDD'):# add hour
                    time_v = time_v + '00'
                if len(time_v) == len('YYYYMMDDHH'):# add minute
                    time_v = time_v + '00'
                """
                grp_date['VARINFO_DATE'].append( time_v)#[:len_date] )
        grp_date = pd.DataFrame.from_dict(grp_date)
        # cast
        grp_date['VARINFO_DATE'] = grp_date['VARINFO_DATE'].astype({'VARINFO_DATE': 'float64'})
        grp_date.sort_values(by=['VARINFO_DATE'],inplace=True)
        grp_date.reset_index(inplace=True,drop=True)
        # insert group
        df_data_grp_id[vInfo1+'__cal'] = numpy.NaN
        for idx in grp_date.index:
            df_data_grp_id.loc[( df_data_grp_id[col_timestamp] > grp_date.loc[idx,'VARINFO_DATE'] ),vInfo1+'__cal'] = grp_date.loc[idx,'GROUP_ID']

    log.info('filter GROUP_ID in VARINFO dataset by first valid values for each variable')
    cnt_changed = 0
    for idxV in firstValid.index:
        vname = firstValid.loc[idxV,'variable'] + '__cal'
        if not vname in df_data_grp_id:
            if not firstValid.loc[idxV,'variable'] == SPECIAL_CASE_VAR_NAME:
                log.warning('[CREATE CALENDAR FOR GROUP_ID] variable %s present in the dataset but missing in calendar_GROUP_ID (missing in the VAR_INFO file) SKIPPED' % (firstValid.loc[idxV,'variable']))
            continue
        ck_condition = (
            (df_data_grp_id['TIMESTAMP_START'] < firstValid.loc[idx,'TIMESTAMP_START']) &
            (df_data_grp_id['TIMESTAMP_START'] != firstValid.loc[idx,'TIMESTAMP_START']) & # not equal
            (pd.isnull(df_data_grp_id[vname]) == 0))
        if sum(ck_condition) > 0:
            log.info('[CREATE CALENDAR FOR GROUP_ID] %d missing GROUP_ID before filter' % (sum(pd.isnull(df_data_grp_id[vname]))))
            log.info('[CREATE CALENDAR FOR GROUP_ID] variable: %s; %d valid value%s in calendarGROUP_ID before the date of the first valid value (%d), replaced with NA(GROUP_ID%s: %s)' % (
                firstValid.loc[idxV,'variable'],
                sum(ck_condition),'s' if sum(ck_condition) > 1 else '',
                firstValid.loc[idx,'TIMESTAMP_START'],
                's' if len(df_data_grp_id.loc[ck_condition,vname].unique().tolist()) > 1 else '',
                '; '.join(['%d' % gx for gx in df_data_grp_id.loc[ck_condition,vname].unique().tolist()])
            ))
            df_data_grp_id.loc[ck_condition,vname] = numpy.NaN
            log.info('[CREATE CALENDAR FOR GROUP_ID] %d missing GROUP_ID after filter' % (sum(pd.isnull(df_data_grp_id[vname]))))
            cnt_changed = cnt_changed + 1
    log.info('%d GROUP_ID%s in VARINFO dataset filtered by first valid values for each variable' % (cnt_changed,'s' if cnt_changed > 1 else ''))
    log.info('filter GROUP_ID in VARINFO dataset by first valid values for each variable ..completed')

    return df_data_grp_id


def run_var_info(path_file_varinfo=None, path_file_data=None, path_00_fp=None, path_file_definitions=None, path_file_pipeline=None, path_file_output=None):
    
    run_time = datetime.datetime.now()
    run_time_str = '%04d%02d%02d%02d%02d%02d' % (
        run_time.year,
        run_time.month,
        run_time.day,
        run_time.hour,
        run_time.minute,
        run_time.second)
    
    log = logging.getLogger(__name__)
    log.info('')
    log.info('path_file_varinfo:     %s' % path_file_varinfo)
    log.info('path_file_data:        %s' % path_file_data)
    log.info('path_file_definitions: %s' % path_file_definitions)
    log.info('path_file_pipeline:    %s' % path_file_pipeline)
    log.info('path_file_output:      %s' % path_file_output)
    log.info('')
    
    # import file from 02_qc_auto and TIMESTAMP_START for the first date valuesfor each variable
    firstValid, data_ts = getFirstValidFrom00fp(path_00_fp)
    
    # import definitions file
    log.info('open DEFINITION file: %s' % (path_file_definitions))
    df_definitions = pd.read_csv(path_file_definitions,sep = '\|\|', encoding='iso-8859-1',engine='python')

    # import VARINFO file
    log.info('open VARINFO file: %s' % (path_file_varinfo))
    # if characger is not valid must be checked line by line
    try:
        df_varinfo = pd.read_csv(path_file_varinfo)
    except UnicodeDecodeError as ex:
        log.error(ex)
        log.warning('some character are not valid (invalid in unicode), find error line')
        # try to read line by line
        nR = 0
        while (1):
            nR = nR + 1
            log.warning('try to read %d line%s' % (nR,'s' if nR > 1 else ''))
            try:
                df_varinfo = pd.read_csv(path_file_varinfo,nrows=nR)
            except:
                log.error('check character to the line %d (invalid unicode)' % nR)
                raise
            
            
    log.info('%d rows in dataset VARINFO' % df_varinfo.shape[0])
    log.info('drop rows with NA')# remove empty
    df_varinfo.dropna(inplace=True)
    log.info('%d rows in dataset VARINFO' % df_varinfo.shape[0])

    # copy original VARINFO
    df_varinfo_original = df_varinfo.copy()

    # fix VAR_INFO_DATE
    for idx in df_varinfo.index:
        if df_varinfo.loc[idx,'VARIABLE'] == 'VAR_INFO_DATE':            
            df_varinfo.loc[idx,'DATAVALUE'] = fixLengthDate(df_varinfo.loc[idx,'DATAVALUE'])            
    # fill missing VARINFO_DATE
    df_varinfo = fillVarInfoDate(df_varinfo,firstValid)
    # remove duplicates inside the groups
    df_varinfo = removeDuplicatesInGROUP_ID(df_varinfo)
    # remove duplicates
    df_varinfo = removeReplicatesGRPvarinfo(df_varinfo)
    # remove duplicates (same VARNAME and DATE but different HEIGHT)
    #df_varinfo = checkVarnameVarHeight(df_varinfo,log)
    # same GROUP_ID ma different VAR_INFO_VARNAME
    df_varinfo = checkMultipleGROUP_ID(df_varinfo)

    # calendar of GROUP_ID for each VAR_INFO_VARNAME
    df_data_grp_id = calendarGROUP_ID(data_ts,df_varinfo,firstValid)
    #log.info('df_data_grp_id.columns')
    #log.info(df_data_grp_id.columns)
    # get informations from ONEFlux_pipeline_*.log as dictionary
    # print('get info:')
    pipeline_infos = dict2ONEFluxPipelineLog(path_file_pipeline)

    # import DATA file
    log.info('open DATA file: %s' % (path_file_data))
    df_data = pd.read_csv(path_file_data)
    col_timestamp = 'TIMESTAMP_START' if 'TIMESTAMP_START' in df_data else 'TIMESTAMP'
    df_data['TIMESTAMP_START_calc'] = df_data[col_timestamp].copy()
    # fix date values (YYYYMMDDHHMN)
    for idx in df_data.index:        
        df_data.loc[idx,'TIMESTAMP_START_calc'] = fixLengthDate(df_data.loc[idx,'TIMESTAMP_START_calc'])        
    df_data['TIMESTAMP_START'] = df_data['TIMESTAMP_START_calc'].copy()
    df_data.drop(columns = ['TIMESTAMP_START_calc'],axis=1,inplace=True)
    col_timestamp = 'TIMESTAMP_START'

    # create BIF
    BIF = {'SITE_ID': [], 'GROUP_ID': [], 'VARIABLE_GROUP': [], 'VARIABLE': [], 'DATAVALUE': []}
    cnt_grp = 0
    # ADD GRP_ONEFLUX
    cnt_grp = cnt_grp + 1
    BIF = addGRP_ONEFLUX(pipeline_infos,cnt_grp,BIF)

    for v_name in df_data.columns:
        if v_name.startswith('TIMESTAMP'):
            continue
        if 'RECO_SR' in v_name:
            log.info('v_name: %s SKIPPED' % v_name)
            continue
        log.info('v_name: %s' % v_name)
        # get information from definition file
        df_definitions_1 = getDefinitionByVariable(v_name,df_definitions)
        if df_definitions_1.shape[0] == 0:
            log.error('%s missing in definition file' % (v_name))
            raise
        # get and fix members
        members = df_definitions_1['Members'].values[0]

        if pd.isnull(members):
            cnt_grp = cnt_grp + 1
            BIF['SITE_ID'].append(pipeline_infos['sitecode'])
            BIF['GROUP_ID'].append(cnt_grp)
            BIF['VARIABLE_GROUP'].append('GRP_VAR_INFO')
            BIF['VARIABLE'].append('VAR_INFO_VARNAME')
            BIF['DATAVALUE'].append(v_name)
            
            BIF['SITE_ID'].append(pipeline_infos['sitecode'])
            BIF['GROUP_ID'].append(cnt_grp)
            BIF['VARIABLE_GROUP'].append('GRP_VAR_INFO')
            BIF['VARIABLE'].append('VAR_INFO_UNIT')
            BIF['DATAVALUE'].append(df_definitions_1['Units'].values[0]) # FROM DEFINITIONS FILE
            
            BIF['SITE_ID'].append(pipeline_infos['sitecode'])
            BIF['GROUP_ID'].append(cnt_grp)
            BIF['VARIABLE_GROUP'].append('GRP_VAR_INFO')
            BIF['VARIABLE'].append('VAR_INFO_DEFINITION')#.append('VAR_INFO_COMMENT')
            BIF['DATAVALUE'].append(df_definitions_1['Description'].values[0]) # FROM DEFINITIONS FILE

            BIF['SITE_ID'].append(pipeline_infos['sitecode'])
            BIF['GROUP_ID'].append(cnt_grp)
            BIF['VARIABLE_GROUP'].append('GRP_VAR_INFO')
            BIF['VARIABLE'].append('VAR_INFO_DATE')

            time_to_add = '%d' % (df_data.loc[df_data.index[0],col_timestamp])
            BIF['DATAVALUE'].append(time_to_add) #[:len('YYYYMMDD')] )# FROM DATASET (if not reported in VARINFO first valid values in YY dataset,format YYYYMMDD)
            continue
        
        # fix members for TS and SWC
        if ((v_name.startswith('TS_F_MDS_'))or(v_name.startswith('SWC_F_MDS_'))):
            members = v_name.replace('_F_MDS_','_')
            members = members.replace('_QC','') if members.endswith('_QC') else members
            log.info('v_name is %s, use Members %s' % (v_name,members))

        # multiple variables in members
        if ')' in members: # multiple options
            members_s = members.split(')')[:-1] # latest is empty
            members_s = [xx2.replace('(','').strip() for xx2 in members_s]
        else:
            members_s = [members]
        # get valid members for variable
        df_varinfo1 = {} # dataframe of the periods of groups
        for nS in range(len(members_s)):
            log.info('try to get informations from variables in dataset: %s' % (members_s[nS]))
            xx = members_s[nS]
            # split variables in group
            if ',' in xx:
                xx_s = xx.split(',')
            else:
                xx_s = [xx]
            xx_s = [xx2.replace('(','').strip() for xx2 in xx_s]
            members_s[nS] = ','.join(xx_s)
            
            log.info('variable %s is calculate by: %s' % (v_name,' or '.join(members_s)))
            if not isinstance(members_s,list):
                members_s = [members_s]
            for grp_members in members_s: # check members in varinfo
                if len(members_s) > 1:
                    log.info('    try to use variables: %s' % grp_members)
                    grp_members = grp_members.split(',')
                    grp_members = [xx.strip() for xx in grp_members]
                if not isinstance(grp_members,list):
                    grp_members = [grp_members]
                # check if all the variables are in VARINFO file
                ck_col = 1
                for xx in grp_members:
                    ck_col = ck_col * sum(df_varinfo['DATAVALUE'] == xx)
                    if ck_col == 0:
                        log.warning('      %s MISSING in VARINFO file, GROUP IS NOT USED %s' % (xx,'(try to use other variable)' if len(members_s) > 1 else ''))
                        break
                    log.info('      %s found VARINFO file' % (xx))
                    ck_col = ck_col * (xx +'__cal' in df_data_grp_id)
                    if ck_col == 0:
                        log.warning('      %s MISSING in DATA files, GROUP IS NOT USED %s' % (xx,'(try to use other variable)' if len(members_s) > 1 else ''))
                        break
                    log.info('      %s found in DATA files of GROUP_ID' % (xx))
                
                if ck_col == 0:
                    break
                # get group of variable in calendar of GROUP_IDs
                df_data_grp_id_tmp = df_data_grp_id[ ['TIMESTAMP_START'] + [qx + '__cal' for qx in grp_members]].copy()
                df_data_grp_id_tmp.set_index('TIMESTAMP_START',inplace=True)
                df_data_tmp = df_data[['TIMESTAMP_START',v_name]].copy()
                df_data_tmp.set_index('TIMESTAMP_START',inplace=True)
                df_data_grp_tmp = pd.concat([df_data_grp_id_tmp, df_data_tmp],axis=1,ignore_index=False)
                df_data_grp_tmp.dropna(inplace=True)
                df_data_grp_tmp.drop(columns = [v_name],inplace=True)
                df_data_grp_tmp.drop_duplicates(inplace=True)
                df_data_grp_tmp.reset_index(inplace=True)
                for tmpQ in df_data_grp_tmp.index:
                    nr_keys = len(df_varinfo1.keys())
                    if not 'k%d' % nr_keys in df_varinfo1.keys():
                        df_varinfo1['k%d' % nr_keys] = df_data_grp_tmp.loc[tmpQ]
                break
            #end for grp_members in members_s: # check members in varinfo
            if ck_col == 1:
                break
        #end for nS in range(len(members_s)):
        #log.info(df_varinfo1)
        #end while len(df_varinfo1) == 0:

        if len(df_varinfo1) == 0:
            # add VAR_INFO_VARNAME missing
            df_varinfo,to_add = addFirstVarInfo(grp_members,firstValid,df_varinfo)
            if len(to_add) == 0:
                to_add = []
                for qx in grp_members:
                    for grp_id_qx in df_varinfo.loc[(df_varinfo['DATAVALUE'] == qx),'GROUP_ID'].unique():
                        to_add.append(df_varinfo.loc[(df_varinfo['GROUP_ID'] == grp_id_qx)])
            to_add = pd.concat(to_add,ignore_index=True)
            df_data_grp_tmp = []
            for to_add_grp in to_add['GROUP_ID'].unique():
                t1 =  to_add.loc[((to_add['GROUP_ID'] == to_add_grp) &
                        (to_add['VARIABLE'] == 'VAR_INFO_DATE')),'DATAVALUE'].values[0]
                v1 =  to_add.loc[((to_add['GROUP_ID'] == to_add_grp) &
                        (to_add['VARIABLE'] == 'VAR_INFO_VARNAME')),'DATAVALUE'].values[0]
                df_data_grp_tmp.append(pd.DataFrame.from_dict({'TIMESTAMP_START': [t1],'%s__cal' % v1: to_add_grp}))
            df_data_grp_tmp = pd.concat(df_data_grp_tmp,ignore_index=True)
            # df_data_grp_tmp = {}
            #    TIMESTAMP_START     TA__cal
            # 0     202306010000  6000000014
            for tmpQ in df_data_grp_tmp.index:
                nr_keys = len(df_varinfo1.keys())
                if not 'k%d' % nr_keys in df_varinfo1.keys():
                    df_varinfo1['k%d' % nr_keys] = df_data_grp_tmp.loc[tmpQ]
            
        for kz,idx_q in df_varinfo1.items():
            temp_df_varinfo_all = []
            temp_df_varinfo_all_original = []
            if isinstance(df_data_grp_tmp.loc[tmpQ],pd.Series):
                for col_idx_q in idx_q.index:
                    if col_idx_q == 'TIMESTAMP_START':
                        continue
                    log.info('get informations from GROUP_ID: %s (VAR_INFO_VARNAME: %s)' % (idx_q[col_idx_q],col_idx_q.replace('__cal','')))
                    temp_df_varinfo = df_varinfo.loc[(df_varinfo['GROUP_ID'] == idx_q[col_idx_q]),['VARIABLE','DATAVALUE']].copy()
                    temp_df_varinfo.set_index('VARIABLE',inplace=True)
                    temp_df_varinfo.columns = [col_idx_q.replace('__cal','')]
                    temp_df_varinfo_all.append(temp_df_varinfo)
                    if sum(df_varinfo_original['GROUP_ID'] == idx_q[col_idx_q]) > 0:
                        temp_df_varinfo = df_varinfo_original.loc[(df_varinfo_original['GROUP_ID'] == idx_q[col_idx_q]),['VARIABLE','DATAVALUE']].copy()
                        temp_df_varinfo.set_index('VARIABLE',inplace=True)
                        temp_df_varinfo.columns = [col_idx_q.replace('__cal','')]
                        temp_df_varinfo_all_original.append(temp_df_varinfo)
            else:
                for col_idx_q in idx_q.columns:
                    if col_idx_q == 'TIMESTAMP_START':
                        continue
                    log.info('get informations from GROUP_ID: %s (VAR_INFO_VARNAME: %s)' % (idx_q[col_idx_q].values[0],col_idx_q.replace('__cal','')))
                    temp_df_varinfo = df_varinfo.loc[(df_varinfo['GROUP_ID'] == idx_q[col_idx_q].values[0]),['VARIABLE','DATAVALUE']].copy()
                    temp_df_varinfo.set_index('VARIABLE',inplace=True)
                    temp_df_varinfo.columns = [col_idx_q.replace('__cal','')]
                    temp_df_varinfo_all.append(temp_df_varinfo)
                    if sum(df_varinfo_original['GROUP_ID'] == idx_q[col_idx_q]) > 0:
                        temp_df_varinfo = df_varinfo_original.loc[(df_varinfo_original['GROUP_ID'] == idx_q[col_idx_q].values[0]),['VARIABLE','DATAVALUE']].copy()
                        temp_df_varinfo.set_index('VARIABLE',inplace=True)
                        temp_df_varinfo.columns = [col_idx_q.replace('__cal','')]
                        temp_df_varinfo_all_original.append(temp_df_varinfo)

            temp_df_varinfo_all = pd.concat(temp_df_varinfo_all,axis=1,ignore_index=False)
            if len(temp_df_varinfo_all_original) > 0:
                temp_df_varinfo_all_original = pd.concat(temp_df_varinfo_all_original,axis=1,ignore_index=False)

            # create string to insert in BIF
            temp_df_varinfo_all['merge'] = numpy.NaN
            for idx_all in temp_df_varinfo_all.index:
                if idx_all == 'VAR_INFO_HEIGHT':
                    vh = temp_df_varinfo_all.loc[idx_all].dropna()
                    if len(vh) == 1:
                        temp_df_varinfo_all.loc[idx_all,'merge'] = vh.values[0]
                    else:
                        vh = '%.2f' % vh.values.astype(float).mean()
                        if vh.endswith('.00'):
                            log.info('special: mean = %s; exported as %s' % (vh,vh[:-1*(len('.00'))]))
                            temp_df_varinfo_all.loc[idx_all,'merge'] = vh[:-1*(len('.00'))]
                        else:
                            temp_df_varinfo_all.loc[idx_all,'merge'] = vh
                    continue
                if idx_all == 'VAR_INFO_DATE':
                    if isinstance(temp_df_varinfo_all_original,list):
                        vh = temp_df_varinfo_all.loc[idx_all].dropna().values.astype(float).max()
                    else:
                        if idx_all in temp_df_varinfo_all_original.index:
                            vh = temp_df_varinfo_all_original.loc[idx_all].dropna().values.astype(float).max()
                        else:
                            vh = temp_df_varinfo_all.loc[idx_all].dropna().values.astype(float).max()
                    temp_df_varinfo_all.loc[idx_all,'merge'] = '%d' % vh
                    continue
                merge1 = []
                for col_XX in temp_df_varinfo_all.columns:
                    if pd.isnull(temp_df_varinfo_all.loc[idx_all,col_XX]):
                        continue
                    if temp_df_varinfo_all.shape[1] == 2: # only one member
                        merge1.append(temp_df_varinfo_all.loc[idx_all,col_XX])
                    else:
                        merge1.append('[%s] %s' % (col_XX,temp_df_varinfo_all.loc[idx_all,col_XX]))
                temp_df_varinfo_all.loc[idx_all,'merge'] = '. '.join(merge1)

            cnt_grp = cnt_grp + 1
            BIF['SITE_ID'].append(pipeline_infos['sitecode'])
            BIF['GROUP_ID'].append(cnt_grp)
            BIF['VARIABLE_GROUP'].append('GRP_VAR_INFO')
            BIF['VARIABLE'].append('VAR_INFO_VARNAME')
            BIF['DATAVALUE'].append(v_name)
            
            BIF['SITE_ID'].append(pipeline_infos['sitecode'])
            BIF['GROUP_ID'].append(cnt_grp)
            BIF['VARIABLE_GROUP'].append('GRP_VAR_INFO')
            BIF['VARIABLE'].append('VAR_INFO_UNIT')
            BIF['DATAVALUE'].append(df_definitions_1['Units'].values[0]) # FROM DEFINITIONS FILE
            
            BIF['SITE_ID'].append(pipeline_infos['sitecode'])
            BIF['GROUP_ID'].append(cnt_grp)
            BIF['VARIABLE_GROUP'].append('GRP_VAR_INFO')
            BIF['VARIABLE'].append('VAR_INFO_DEFINITION')#.append('VAR_INFO_COMMENT')
            BIF['DATAVALUE'].append(df_definitions_1['Description'].values[0]) # FROM DEFINITIONS FILE

            BIF['SITE_ID'].append(pipeline_infos['sitecode'])
            BIF['GROUP_ID'].append(cnt_grp)
            BIF['VARIABLE_GROUP'].append('GRP_VAR_INFO')
            BIF['VARIABLE'].append('VAR_INFO_DATE')
            BIF['DATAVALUE'].append(temp_df_varinfo_all.loc['VAR_INFO_DATE','merge']) # from VAR_INFO
            
            for info_to_add in ['VAR_INFO_COMMENT','VAR_INFO_AGG_NUMLOC','VAR_INFO_HEIGHT','VAR_INFO_MODEL']:
                if not info_to_add in temp_df_varinfo_all.index:
                    continue
                if pd.isnull(temp_df_varinfo_all.loc[info_to_add,'merge']):
                    continue
                BIF['SITE_ID'].append(pipeline_infos['sitecode'])
                BIF['GROUP_ID'].append(cnt_grp)
                BIF['VARIABLE_GROUP'].append('GRP_VAR_INFO')
                BIF['VARIABLE'].append(info_to_add)
                BIF['DATAVALUE'].append(temp_df_varinfo_all.loc[info_to_add,'merge']) # FROM VARINFO
        #end for idx_qN in range(len(df_varinfo1)):

    BIF = pd.DataFrame.from_dict(BIF)
    # remove duplicates
    BIF = removeReplicatesGRPvarinfo(BIF)
    # remove duplicates (same VARNAME and DATE but different HEIGHT)
    #BIF = checkVarnameVarHeight(BIF,log)
    if not os.path.exists( os.path.dirname(path_file_output) ):
        os.makedirs( os.path.dirname(path_file_output),exist_ok=True)
    BIF.to_csv(path_file_output,index=False)
    # log.info('')
    log.info('write file: %s' % path_file_output)
    # log.info('')
    # # logging.shutdown()
    # # # write sintesi_log
    # sint_file_log = []
    # with open(file_log) as flog:
    #     for line in flog.readlines():
    #         line = line.replace('\n','').replace('\r','')
    #         line_s = line.split('::')[-1]
    #         if (
    #             ('path_file_varinfo' in line) or
    #             ('path_file_data' in line) or
    #             ('path_file_definitions' in line) or
    #             (path_file_pipeline in line) or
    #             (path_file_output in line)):
    #             sint_file_log.append(line_s)
    #             continue
    #         if (('ERROR' in line) or ('WARNING' in line)):
    #             sint_file_log.append(line_s)
    # with open(os.path.join(os.path.dirname(file_log),'synth__' + os.path.basename(file_log)),'w') as flog2:
    #     for xx in sint_file_log:
    #         flog2.write('%s\n' % xx)
    # log.info('write file: %s' % os.path.join(os.path.dirname(file_log),'synth__' + os.path.basename(file_log)))

