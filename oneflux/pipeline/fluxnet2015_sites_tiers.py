'''
oneflux.pipeline.fluxnet2015_sites_tiers

For license information:
see LICENSE file or headers in oneflux.__init__.py

FLUXNET2015 sites and tiers information (December 2015 release)

@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2016-04-26
'''
import sys
import socket
import logging

from oneflux import ONEFluxError

log = logging.getLogger(__name__)

HOSTNAME = socket.gethostname()

ERA_FIRST_TIMESTAMP_START = '198901010000'
ERA_LAST_TIMESTAMP_START = '201512312330'

SITE_LISTS = {
    'todo': ['US-ORv'],

#    'olaf1': ['AR-SLu', 'AR-Vir', 'AT-Neu', 'AU-Ade', 'AU-ASM', 'AU-Cpr', 'AU-Cum', 'AU-DaP', 'AU-DaS', 'AU-Dry', 'AU-Emr', 'AU-Fog', 'AU-Gin', 'AU-GWW', 'AU-How', 'AU-Lox', ],
#    'olaf2': ['AU-RDF', 'AU-Rig', 'AU-Rob', 'AU-Stp', 'AU-TTE', 'AU-Tum', 'AU-Wac', 'AU-Whr', 'AU-Wom', 'AU-Ync', 'BE-Bra', 'BE-Lon', ],
#    'olaf3': ['BE-Vie', 'BR-Sa1', 'BR-Sa3', 'CA-Gro', 'CA-Man', 'CA-NS1', 'CA-NS2', 'CA-NS3', 'CA-NS4', 'CA-NS5', 'CA-NS6', 'CA-NS7', ],
#    'rocky1': ['CA-Oas', 'CA-Obs', 'CA-Qfo', 'CA-SF1', 'CA-SF2', 'CA-SF3', ],
#    'rocky2': ['CA-TP1', 'CA-TP2', 'CA-TP3', 'CA-TP4', 'CA-TPD', 'CG-Tch', ],
#    'rocky3': ['CH-Cha', 'CH-Dav', 'CH-Fru', 'CH-Lae', ],
#    'rocky4': ['CH-Oe1', 'CH-Oe2', 'CN-Cha', 'CN-Cng', 'CN-Dan', 'CN-Din', 'CN-Du2', 'CN-Du3', 'CN-Ha2', 'CN-HaM', 'CN-Qia', 'CN-Sw2', ],
#    'rocky5': ['CZ-BK1', 'CZ-BK2', 'CZ-wet', 'DE-Akm', 'DE-Geb', ],
#    'dash1': ['DE-Gri', 'DE-Hai', 'DE-Kli', 'DE-Lkb', 'DE-Lnf', ],
#    'dash2': ['DE-Obe', 'DE-RuR', 'DE-RuS', 'DE-Seh', 'DE-SfN', 'DE-Spw', 'DE-Tha', 'DE-Zrk', 'DK-Eng', ],
#    'dash3': ['DK-Fou', 'DK-NuF', 'DK-Sor', 'DK-ZaF', 'DK-ZaH', 'ES-Amo', ],
#    'dash4': ['ES-LgS', 'ES-LJu', 'ES-Ln2', 'FI-Hyy', 'FI-Jok', 'FI-Let', 'FI-Lom', ],
#    'dash5': ['FI-Sod', 'FR-Fon', 'FR-Gri', 'FR-LBr', ],
#    'polly1': ['FR-Pue', 'GF-Guy', 'GH-Ank', 'IT-BCi', 'IT-CA1', 'IT-CA2', 'IT-CA3', ],
#    'polly2': ['IT-Col', 'IT-Cp2', 'IT-Cpz', 'IT-Isp', 'IT-La2', 'IT-Lav', 'IT-MBo', ],
#    'polly3': ['IT-Noe', 'IT-PT1', 'IT-Ren', 'IT-Ro1', 'IT-Ro2', 'IT-SR2', 'IT-SRo', 'IT-Tor', ],
#    'polly4': ['JP-MBF', 'JP-SMF', 'MY-PSO', 'NL-Hor', 'NL-Loo', 'NO-Adv', 'NO-Blv', 'PA-SPn', 'PA-SPs', 'RU-Che', 'RU-Cok', ],
#    'coors1': ['RU-Fyo', 'RU-Ha1', 'RU-Sam', 'RU-SkP', 'RU-Tks', 'RU-Vrk', 'SD-Dem', 'SE-St1', 'SN-Dhr', 'US-AR1', 'US-AR2', 'US-ARb', 'US-ARc', ],
#    'coors2': ['US-ARM', 'US-Atq', 'US-Blo', 'US-Cop', 'US-CRT', 'US-GBT', 'US-GLE', 'US-Goo', ],
#    'coors3': ['US-Ha1', 'US-IB2', 'US-Ivo', 'US-KS1', 'US-KS2', 'US-Lin', 'US-Los', 'US-LWW', ],
#    'coors4': ['US-Me1', 'US-Me2', 'US-Me3', 'US-Me4', 'US-Me5', 'US-Me6', 'US-MMS', 'US-Myb', ],
#    'doright1': ['US-Ne1', 'US-Ne2', 'US-Ne3', 'US-NR1', ],
#    'doright2': ['US-Oho', 'US-ORv', 'US-PFa', 'US-Prr', 'US-SRC', 'US-SRG', ],
#    'doright3': ['US-SRM', 'US-Sta', 'US-Syv', 'US-Ton', 'US-Tw1', 'US-Tw2', 'US-Tw3', 'US-Tw4', 'US-Twt', ],
#    'doright4': ['US-UMB', 'US-UMd', 'US-Var', 'US-WCr', 'US-Whs', ],
#    'doright5': ['US-Wi0', 'US-Wi1', 'US-Wi2', 'US-Wi3', 'US-Wi4', 'US-Wi5', 'US-Wi6', 'US-Wi7', 'US-Wi8', 'US-Wi9', 'US-Wkg', 'US-WPT', 'ZA-Kru', 'ZM-Mon', ],


    # ALL
    'all_jul2016': [
        'AR-SLu', 'AR-Vir', 'AT-Neu', 'AU-ASM', 'AU-Ade', 'AU-Cpr', 'AU-Cum', 'AU-DaP', 'AU-DaS',
        'AU-Dry', 'AU-Emr', 'AU-Fog', 'AU-GWW', 'AU-Gin', 'AU-How', 'AU-Lox', 'AU-RDF', 'AU-Rig',
        'AU-Rob', 'AU-Stp', 'AU-TTE', 'AU-Tum', 'AU-Wac', 'AU-Whr', 'AU-Wom', 'AU-Ync', 'BE-Bra',
        'BE-Lon', 'BE-Vie', 'BR-Sa1', 'BR-Sa3', 'CA-Gro', 'CA-Man', 'CA-NS1', 'CA-NS2', 'CA-NS3',
        'CA-NS4', 'CA-NS5', 'CA-NS6', 'CA-NS7', 'CA-Oas', 'CA-Obs', 'CA-Qfo', 'CA-SF1', 'CA-SF2',
        'CA-SF3', 'CA-TP1', 'CA-TP2', 'CA-TP3', 'CA-TP4', 'CA-TPD', 'CG-Tch', 'CH-Cha', 'CH-Dav',
        'CH-Fru', 'CH-Lae', 'CH-Oe1', 'CH-Oe2', 'CN-Cha', 'CN-Cng', 'CN-Dan', 'CN-Din', 'CN-Du2',
        'CN-Du3', 'CN-Ha2', 'CN-HaM', 'CN-Qia', 'CN-Sw2', 'CZ-BK1', 'CZ-BK2', 'CZ-wet', 'DE-Akm',
        'DE-Geb', 'DE-Gri', 'DE-Hai', 'DE-Kli', 'DE-Lkb', 'DE-Lnf', 'DE-Obe', 'DE-RuR', 'DE-RuS',
        'DE-Seh', 'DE-SfN', 'DE-Spw', 'DE-Tha', 'DE-Zrk', 'DK-Eng', 'DK-Fou', 'DK-NuF', 'DK-Sor',
        'DK-ZaF', 'DK-ZaH', 'ES-Amo', 'ES-LJu', 'ES-LgS', 'ES-Ln2', 'FI-Hyy', 'FI-Jok', 'FI-Let',
        'FI-Lom', 'FI-Sod', 'FR-Fon', 'FR-Gri', 'FR-LBr', 'FR-Pue', 'GF-Guy', 'GH-Ank', 'IT-BCi',
        'IT-CA1', 'IT-CA2', 'IT-CA3', 'IT-Col', 'IT-Cp2', 'IT-Cpz', 'IT-Isp', 'IT-La2', 'IT-Lav',
        'IT-MBo', 'IT-Noe', 'IT-PT1', 'IT-Ren', 'IT-Ro1', 'IT-Ro2', 'IT-SR2', 'IT-SRo', 'IT-Tor',
        'JP-MBF', 'JP-SMF', 'MY-PSO', 'NL-Hor', 'NL-Loo', 'NO-Adv', 'NO-Blv', 'PA-SPn', 'PA-SPs',
        'RU-Che', 'RU-Cok', 'RU-Fyo', 'RU-Ha1', 'RU-Sam', 'RU-SkP', 'RU-Tks', 'RU-Vrk', 'SD-Dem',
        'SE-St1', 'SN-Dhr', 'US-AR1', 'US-AR2', 'US-ARM', 'US-ARb', 'US-ARc', 'US-Atq', 'US-Blo',
        'US-CRT', 'US-Cop', 'US-GBT', 'US-GLE', 'US-Goo', 'US-Ha1', 'US-IB2', 'US-Ivo', 'US-KS1',
        'US-KS2', 'US-LWW', 'US-Lin', 'US-Los', 'US-MMS', 'US-Me1', 'US-Me2', 'US-Me3', 'US-Me4',
        'US-Me5', 'US-Me6', 'US-Myb', 'US-NR1', 'US-Ne1', 'US-Ne2', 'US-Ne3', 'US-ORv', 'US-Oho',
        'US-PFa', 'US-Prr', 'US-SRC', 'US-SRG', 'US-SRM', 'US-Sta', 'US-Syv', 'US-Ton', 'US-Tw1',
        'US-Tw2', 'US-Tw3', 'US-Tw4', 'US-Twt', 'US-UMB', 'US-UMd', 'US-Var', 'US-WCr', 'US-WPT',
        'US-Whs', 'US-Wi0', 'US-Wi1', 'US-Wi2', 'US-Wi3', 'US-Wi4', 'US-Wi5', 'US-Wi6', 'US-Wi7',
        'US-Wi8', 'US-Wi9', 'US-Wkg', 'ZA-Kru', 'ZM-Mon', ],
    'all_apr2016':[
        'AR-SLu', 'AR-Vir', 'AT-Neu', 'AU-ASM', 'AU-Ade', 'AU-Cpr', 'AU-Cum', 'AU-DaP', 'AU-DaS',
        'AU-Dry', 'AU-Emr', 'AU-Fog', 'AU-GWW', 'AU-RDF', 'AU-Rig', 'AU-Rob', 'AU-Tum', 'AU-Whr',
        'BE-Bra', 'BE-Lon', 'BE-Vie', 'BR-Sa1', 'BR-Sa3', 'CA-Gro', 'CA-NS1', 'CA-NS2', 'CA-NS3',
        'CA-NS4', 'CA-NS5', 'CA-NS6', 'CA-NS7', 'CA-Qfo', 'CA-SF1', 'CA-SF2', 'CA-SF3', 'CA-TP1',
        'CA-TP2', 'CA-TP3', 'CA-TPD', 'CG-Tch', 'CH-Cha', 'CH-Fru', 'CH-Oe1', 'CN-Cha', 'CN-Cng',
        'CN-Dan', 'CN-Din', 'CN-Du2', 'CN-Du3', 'CN-Ha2', 'CN-HaM', 'CN-Qia', 'CN-Sw2', 'CZ-BK1',
        'CZ-BK2', 'DE-Akm', 'DE-Gri', 'DE-Hai', 'DE-Kli', 'DE-Lkb', 'DE-Obe', 'DE-RuS', 'DE-SfN',
        'DE-Spw', 'DE-Tha', 'DE-Zrk', 'DK-Eng', 'DK-NuF', 'DK-Sor', 'DK-ZaF', 'DK-ZaH', 'ES-Amo',
        'ES-LJu', 'ES-LgS', 'ES-Ln2', 'FI-Hyy', 'FI-Jok', 'FR-Fon', 'FR-Gri', 'FR-Pue', 'GF-Guy',
        'GH-Ank', 'IT-BCi', 'IT-CA1', 'IT-CA2', 'IT-CA3', 'IT-Cp2', 'IT-Isp', 'IT-La2', 'IT-Lav',
        'IT-Noe', 'IT-PT1', 'IT-Ren', 'IT-Ro1', 'IT-Ro2', 'IT-SR2', 'IT-SRo', 'IT-Tor', 'JP-MBF',
        'JP-SMF', 'MY-PSO', 'NL-Hor', 'NL-Loo', 'NO-Adv', 'PA-SPn', 'PA-SPs', 'RU-Che', 'RU-Cok',
        'RU-Fyo', 'RU-Ha1', 'RU-Sam', 'RU-SkP', 'RU-Vrk', 'SD-Dem', 'SE-St1', 'US-AR1', 'US-AR2',
        'US-ARM', 'US-Atq', 'US-Blo', 'US-CRT', 'US-Cop', 'US-Goo', 'US-Ha1', 'US-IB2', 'US-Ivo',
        'US-KS2', 'US-LWW', 'US-Lin', 'US-Los', 'US-MMS', 'US-Me1', 'US-Me2', 'US-Me6', 'US-Myb',
        'US-NR1', 'US-Ne1', 'US-Ne2', 'US-Ne3', 'US-Oho', 'US-PFa', 'US-SRC', 'US-SRG', 'US-SRM',
        'US-Sta', 'US-Syv', 'US-Ton', 'US-Tw1', 'US-Tw2', 'US-Tw3', 'US-Twt', 'US-UMB', 'US-UMd',
        'US-Var', 'US-WCr', 'US-WPT', 'US-Whs', 'US-Wi0', 'US-Wi3', 'US-Wi4', 'US-Wi6', 'US-Wi9',
        'US-Wkg', 'ZA-Kru', 'ZM-Mon', ],
    'ameriflux': [
        'BR-Sa1', 'BR-Sa3', 'CA-Gro', 'CA-Man', 'CA-NS1', 'CA-NS2', 'CA-NS3', 'CA-NS4', 'CA-NS5', 'CA-NS6',
        'CA-NS7', 'CA-Oas', 'CA-Obs', 'CA-Qfo', 'CA-SF1', 'CA-SF2', 'CA-SF3', 'CA-TP1', 'CA-TP2', 'CA-TP3',
        'CA-TP4', 'CA-TPD', 'US-AR1', 'US-AR2', 'US-ARM', 'US-ARb', 'US-ARc', 'US-Atq', 'US-Blo', 'US-CRT',
        'US-Cop', 'US-GBT', 'US-GLE', 'US-Goo', 'US-Ha1', 'US-IB2', 'US-Ivo', 'US-KS1', 'US-KS2', 'US-LWW',
        'US-Lin', 'US-Los', 'US-MMS', 'US-Me1', 'US-Me2', 'US-Me3', 'US-Me4', 'US-Me5', 'US-Me6', 'US-Myb',
        'US-NR1', 'US-Ne1', 'US-Ne2', 'US-Ne3', 'US-ORv', 'US-Oho', 'US-PFa', 'US-Prr', 'US-SRC', 'US-SRG',
        'US-SRM', 'US-Sta', 'US-Syv', 'US-Ton', 'US-Tw1', 'US-Tw2', 'US-Tw3', 'US-Tw4', 'US-Twt', 'US-UMB',
        'US-UMd', 'US-Var', 'US-WCr', 'US-WPT', 'US-Whs', 'US-Wi0', 'US-Wi1', 'US-Wi2', 'US-Wi3', 'US-Wi4',
        'US-Wi5', 'US-Wi6', 'US-Wi7', 'US-Wi8', 'US-Wi9', 'US-Wkg', ],
}


SITES_TIERS_FOLDERS = [
###DB  SITEID  FIRST_YEAR  LAST_YEAR   TIER    VERSION CURRENT_FOLDER
"OTHER   AR-SLu  2009    2011    TIER1   1   AR-SLu_processamento_completato_il_20160307_zip",
"OTHER   AR-Vir  2009    2012    TIER1   1   AR-Vir_processed_on_20160613_zip",
"EUDB    AT-Neu  2002    2012    TIER1   1   AT-Neu_processed_on_20160711",
"OTHER   AU-Ade  2007    2009    TIER1   1   AU-Ade_processed_on_20160613_zip",
"OTHER   AU-ASM  2010    2013    TIER1   2   AU-ASM_processed_on_20160627",
"OTHER   AU-ASM  2014    2014    TIER2   2   AU-ASM_processed_on_20160627",
"OTHER   AU-Cpr  2010    2014    TIER1   2   AU-Cpr_processed_on_20160819",
"OTHER   AU-Cum  2012    2014    TIER1   2   AU-Cum_processed_on_20160818",
"OTHER   AU-DaP  2007    2013    TIER1   2   AU-DaP_processed_on_20160819",
"OTHER   AU-DaS  2008    2014    TIER1   2   AU-DaS_processed_on_20160819",
"OTHER   AU-Dry  2008    2014    TIER1   2   AU-Dry_processed_on_20160614",
"OTHER   AU-Emr  2011    2013    TIER1   1   AU-Emr_processamento_completato_il_20160311_zip",
"OTHER   AU-Fog  2006    2008    TIER1   1   AU-Fog_processed_on_20160623_zip",
"OTHER   AU-Gin  2011    2014    TIER1   1   AU-Gin_processed_on_20160627",
"OTHER   AU-GWW  2013    2014    TIER1   1   AU-GWW_processed_on_20160623_zip",
"OTHER   AU-How  2001    2014    TIER1   1   AU-How_processed_on_20160819",
"OTHER   AU-Lox  2008    2009    TIER1   1   AU-Lox_processed_on_20160819",
"OTHER   AU-RDF  2011    2013    TIER1   1   AU-RDF_processed_on_20160623_zip",
"OTHER   AU-Rig  2011    2014    TIER1   2   AU-Rig_data20160817_processed_on_20160825",
"OTHER   AU-Rob  2014    2014    TIER1   1   AU-Rob_processamento_completato_il_20160322_zip",
"OTHER   AU-Stp  2008    2014    TIER1   1   AU-Stp_data20160817_processed_on_20160822",
"OTHER   AU-TTE  2012    2013    TIER1   1   AU-TTE_processed_on_20160819",
"OTHER   AU-TTE  2014    2014    TIER2   1   AU-TTE_processed_on_20160819",
"OTHER   AU-Tum  2001    2014    TIER1   2   AU-Tum_data20160817_processed_on_20160826",
"OTHER   AU-Wac  2005    2008    TIER1   1   AU-Wac_processed_on_20160819",
"OTHER   AU-Whr  2011    2014    TIER1   2   AU-Whr_data20160817",
"OTHER   AU-Wom  2010    2012    TIER1   1   AU-Wom_20160509_processed_on_20160901",
"OTHER   AU-Wom  2013    2014    TIER2   1   AU-Wom_20160509_processed_on_20160901",
"OTHER   AU-Ync  2012    2014    TIER1   1   AU-Ync_data_20160831_processed_on_20160901",
"EUDB    BE-Bra  1996    2014    TIER1   2   BE-Bra_processed_on_20160702",
"EUDB    BE-Lon  2004    2014    TIER1   1   BE-Lon_processamento_completato_il_20160301_con_dataset_fino_al_2014_zip",
"EUDB    BE-Vie  1996    2014    TIER1   1   BE-Vie_processamento_completato_il_20160301_con_dataset_fino_al_2014_zip",
"AMERIFLUX   BR-Sa1  2002    2011    TIER2   1   BR-Sa1_no_2007_processamento_completato_il_20160506_zip",
"AMERIFLUX   BR-Sa3  2000    2004    TIER1   1   BR-Sa3_processed_on_20160801",
"AMERIFLUX   CA-Gro  2003    2014    TIER2   1   CA-Gro_processamento_completato_il_20160510_zip",
"AMERIFLUX   CA-Man  1994    2008    TIER1   1   CA-Man_processed_on_20160825",
"AMERIFLUX   CA-NS1  2001    2005    TIER1   2   CA-NS1_processamento_completato_il_20160510_zip",
"AMERIFLUX   CA-NS2  2001    2005    TIER1   1   CA-NS2_processamento_completato_il_20160511_zip",
"AMERIFLUX   CA-NS3  2001    2005    TIER1   1   CA-NS3_processamento_completato_il_20160511_zip",
"AMERIFLUX   CA-NS4  2002    2005    TIER1   1   CA-NS4_processamento_completato_il_20160511_zip",
"AMERIFLUX   CA-NS5  2001    2005    TIER1   1   CA-NS5_processamento_completato_il_20160513_zip",
"AMERIFLUX   CA-NS6  2001    2005    TIER1   1   CA-NS6_processamento_completato_il_20160513_zip",
"AMERIFLUX   CA-NS7  2002    2005    TIER1   1   CA-NS7_processamento_completato_il_20160513_zip",
"AMERIFLUX   CA-Oas  1996    2010    TIER2   1   CA-Oas_processed_on_20160720",
"AMERIFLUX   CA-Obs  1997    2010    TIER2   1   CA-Obs-20160721-ready_processed_on_20160803",
"AMERIFLUX   CA-Qfo  2003    2010    TIER1   1   CA-Qfo_processamento_completato_il_20160516_zip",
"AMERIFLUX   CA-SF1  2003    2006    TIER1   1   CA-SF1_processamento_completato_il_20160516_zip",
"AMERIFLUX   CA-SF2  2001    2005    TIER1   1   CA-SF2_processamento_completato_il_20160516_zip",
"AMERIFLUX   CA-SF3  2001    2006    TIER1   1   CA-SF3_processamento_completato_il_20160516_zip",
"AMERIFLUX   CA-TP1  2002    2014    TIER2   2   CA-TP1_processed_on_20160816",
"AMERIFLUX   CA-TP2  2002    2007    TIER2   1   CA-TP2_processamento_completato_il_20160502_zip",
"AMERIFLUX   CA-TP3  2002    2014    TIER2   1   CA-TP3-20160311-ready_tolto_il_2015_processamento_completato_il_20160407_zip_no_2002_URE",
"AMERIFLUX   CA-TP4  2002    2014    TIER2   1   CA-TP4_processed_on_20160718",
"AMERIFLUX   CA-TPD  2012    2014    TIER2   1   CA-TPD_tolto_il_2015_processamento_completato_il_20160331_zip",
"EUDB    CG-Tch  2006    2009    TIER2   1   CG-Tch_processed_on_20160720",
"EUDB    CH-Cha  2005    2014    TIER1   2   CH-Cha_processed_on_20160629",
"EUDB    CH-Dav  1997    2014    TIER1   1   CH-Dav_processed_on_20160711",
"EUDB    CH-Fru  2005    2014    TIER1   2   CH-Fru_processed_on_20160801",
"EUDB    CH-Lae  2004    2014    TIER1   1   CH-Lae_processed_on_20160810",
"EUDB    CH-Oe1  2002    2008    TIER1   2   CH-Oe1_ex20161014_proc20161017",
"EUDB    CH-Oe2  2004    2014    TIER1   1   CH-Oe2_processed_on_20160825",
"OTHER   CN-Cha  2003    2005    TIER1   1   CN-Cha_processamento_completato_il_20160223_zip",
"OTHER   CN-Cng  2007    2010    TIER1   1   CN-Cng_processamento_completato_il_20160224_zip",
"OTHER   CN-Dan  2004    2005    TIER1   1   CN-Dan_processamento_completato_il_20160224_zip",
"OTHER   CN-Din  2003    2005    TIER1   1   CN-Din_processamento_completato_il_20160225_zip",
"OTHER   CN-Du2  2006    2008    TIER1   1   CN-Du2_processamento_completato_il_20160225_zip",
"OTHER   CN-Du3  2009    2010    TIER2   1   CN-Du3_processamento_completato_il_20160226_zip",
"OTHER   CN-Ha2  2003    2005    TIER1   1   CN-Ha2_processamento_completato_il_20160228_zip",
"OTHER   CN-HaM  2002    2004    TIER1   1   CN-HaM_processamento_completato_il_20160228_zip",
"OTHER   CN-Qia  2003    2005    TIER1   1   CN-Qia_processamento_completato_il_20160228_zip",
"OTHER   CN-Sw2  2010    2012    TIER1   1   CN-Sw2_processamento_completato_il_20160301_zip",
"EUDB    CZ-BK1  2004    2008    TIER1   2   CZ-BK1_processamento_completato_il_20160426_zip",
"EUDB    CZ-BK1  2009    2014    TIER2   2   CZ-BK1_processamento_completato_il_20160426_zip",
"EUDB    CZ-BK2  2004    2006    TIER1   2   CZ-BK2_processed_on_20160721",
"EUDB    CZ-BK2  2007    2012    TIER2   2   CZ-BK2_processed_on_20160721",
"EUDB    CZ-wet  2006    2014    TIER1   1   CZ-wet_processed_on_20160825",
"EUDB    DE-Akm  2009    2014    TIER1   1   DE-Akm_processed_on_20160721",
"EUDB    DE-Geb  2001    2014    TIER1   1   DE-Geb_processed_on_20160815",
"EUDB    DE-Gri  2004    2014    TIER1   1   DE-Gri_processed_on_20160805",
"EUDB    DE-Hai  2000    2012    TIER1   1   DE-Hai_processed_on_20160712",
"EUDB    DE-Kli  2004    2014    TIER1   1   DE-Kli_processed_on_20160722",
"EUDB    DE-Lkb  2009    2013    TIER1   1   DE-Lkb_processed_on_20160721",
"EUDB    DE-Lnf  2002    2012    TIER2   1   DE-Lnf_processed_on_20160825",
"EUDB    DE-Obe  2008    2014    TIER1   1   DE-Obe_processed_on_20160722",
"EUDB    DE-RuR  2011    2014    TIER1   1   DE-RuR_processed_on_20160817",
"EUDB    DE-RuS  2011    2014    TIER1   1   DE-RuS_processed_on_20160722",
"EUDB    DE-Seh  2007    2010    TIER1   1   DE-Seh_processed_on_20160826",
"EUDB    DE-SfN  2012    2014    TIER1   1   DE-SfN_processamento_completato_il_20160420_zip",
"EUDB    DE-Spw  2010    2014    TIER1   1   DE-Spw_processed_on_20160722",
"EUDB    DE-Tha  1996    2014    TIER1   1   DE-Tha_processed_on_20160805",
"EUDB    DE-Zrk  2013    2014    TIER2   2   DE-Zrk_processamento_completato_il_20160427_zip",
"EUDB    DK-Eng  2005    2008    TIER2   1   DK-Eng_processed_on_20160721",
"EUDB    DK-Fou  2005    2005    TIER1   1   DK-Fou_processed_on_20160427",
"EUDB    DK-NuF  2008    2014    TIER1   1   DK-NuF_processed_on_20160801",
"EUDB    DK-Sor  1996    2014    TIER1   2   DK-Sor_processed_on_20160614_zip",
"EUDB    DK-ZaF  2008    2011    TIER1   2   DK-ZaF_processed_on_20160811",
"EUDB    DK-ZaH  2000    2014    TIER1   2   DK-ZaH_processamento_completato_il_20160421_zip",
"EUDB    ES-Amo  2007    2012    TIER2   1   ES-Amo_processed_on_20160722",
"EUDB    ES-LgS  2007    2009    TIER1   1   ES-LgS_processed_on_20160801",
"EUDB    ES-LJu  2004    2013    TIER2   1   ES-LJu_processed_on_20160801",
"EUDB    ES-Ln2  2009    2009    TIER1   1   ES-Ln2_processed_on_20160722",
"EUDB    FI-Hyy  1996    2014    TIER1   1   FI-Hyy_processed_on_20160804",
"EUDB    FI-Jok  2000    2003    TIER1   1   FI-Jok_processed_on_20160801",
"EUDB    FI-Let  2009    2012    TIER2   1   FI-Let_processed_on_20160826",
"EUDB    FI-Lom  2007    2009    TIER1   1   FI-Lom_processed_on_20160826",
"EUDB    FI-Sod  2001    2014    TIER1   1   FI-Sod_processed_on_20160826",
"EUDB    FR-Fon  2005    2014    TIER1   1   FR-Fon_processamento_completato_il_20160420_zip",
"EUDB    FR-Gri  2004    2013    TIER1   1   FR-Gri_processed_20160527_zip",
"EUDB    FR-Gri  2014    2014    TIER2   1   FR-Gri_processed_20160527_zip",
"EUDB    FR-LBr  1996    2008    TIER1   1   FR-LBr_processed_on_20160830",
"EUDB    FR-Pue  2000    2014    TIER1   2   FR-Pue_processamento_completato_il_20160429_zip",
"EUDB    GF-Guy  2004    2014    TIER1   2   GF-Guy_processamento_completato_il_20160427_zip",
"EUDB    GH-Ank  2011    2014    TIER2   1   GH-Ank_processamento_completato_il_20160518_zip",
"EUDB    IT-BCi  2004    2014    TIER1   2   IT-BCi_processed_on_20160810",
"EUDB    IT-CA1  2011    2014    TIER1   2   IT-CA1_processamento_completato_il_20160429_zip",
"EUDB    IT-CA2  2011    2014    TIER1   2   IT-CA2_processed_on_20160801",
"EUDB    IT-CA3  2011    2014    TIER1   2   IT-CA3_processed_on_20160801",
"EUDB    IT-Col  1996    2014    TIER1   1   IT-Col_ex20160504_proc20161024",
"EUDB    IT-Cp2  2012    2014    TIER1   2   IT-Cp2_processamento_completato_il_20160429_zip",
"EUDB    IT-Cpz  1997    2009    TIER1   1   IT-Cpz_processed_on_20160830",
"EUDB    IT-Isp  2013    2014    TIER1   1   IT-Isp_processamento_completato_il_20150928_con_dataset_fino_al_2014_zip",
"EUDB    IT-La2  2000    2002    TIER1   1   IT-La2_processed_on_20160801",
"EUDB    IT-Lav  2003    2014    TIER1   2   IT-Lav_processamento_completato_il_20160303_con_dataset_fino_al_2014_zip",
"EUDB    IT-MBo  2003    2013    TIER1   1   IT-MBo_processed_on_20160831",
"EUDB    IT-Noe  2004    2014    TIER1   2   IT-Noe_processamento_completato_il_20160426_zip",
"EUDB    IT-PT1  2002    2004    TIER1   1   IT-PT1_processed_on_20160801",
"EUDB    IT-Ren  1998    2013    TIER1   1   IT-Ren_processed_on_20160805",
"EUDB    IT-Ro1  2000    2008    TIER1   1   IT-Ro1_processed_on_20160804",
"EUDB    IT-Ro2  2002    2012    TIER1   1   IT-Ro2_processed_on_20160811",
"EUDB    IT-SR2  2013    2014    TIER1   1   IT-SR2_processed_on_20160805",
"EUDB    IT-SRo  1999    2012    TIER1   1   IT-SRo_processed_on_20160810",
"EUDB    IT-Tor  2008    2014    TIER1   2   IT-Tor_processed_on_20160815",
"OTHER   JP-MBF  2003    2005    TIER1   1   JP-MBF_processed_on_20160801",
"OTHER   JP-SMF  2002    2006    TIER1   1   JP-SMF_processed_on_20160801",
"OTHER   MY-PSO  2003    2009    TIER2   1   MY-PSO_processed_on_20160801",
"EUDB    NL-Hor  2004    2011    TIER1   1   NL-Hor_processed_on_20160802",
"EUDB    NL-Loo  1996    2013    TIER1   1   NL-Loo_processed_on_20160810",
"EUDB    NL-Loo  2014    2014    TIER2   1   NL-Loo_processed_on_20160810",
"EUDB    NO-Adv  2011    2014    TIER1   1   NO-Adv_processed_on_20160702",
"EUDB    NO-Blv  2008    2009    TIER1   1   NO-Blv_processed_on_20160820",
"EUDB    PA-SPn  2007    2009    TIER2   1   PA-SPn_processed_on_20160802",
"EUDB    PA-SPs  2007    2009    TIER2   1   PA-SPs_processed_on_20160802",
"EUDB    RU-Che  2002    2005    TIER1   1   RU-Che_processed_on_20160803",
#"EUDB    RU-Cok  2003    2014    TIER1   2   RU-Cok_processed_on_20160825", # RU-Cok only met/heat data in 2014?
"EUDB    RU-Cok  2003    2013    TIER1   2   RU-Cok_processed_on_20160825",
"EUDB    RU-Fyo  1998    2014    TIER1   2   RU-Fyo_processamento_completato_il_20160303_con_dataset_fino_al_2014_zip",
"EUDB    RU-Ha1  2002    2004    TIER1   1   RU-Ha1_processed_on_20160802",
"EUDB    RU-Sam  2002    2014    TIER2   1   RU-Sam_processamento_completato_il_20150930_con_dataset_fino_al_2014_zip",
"EUDB    RU-SkP  2012    2014    TIER2   1   RU-SkP_processed_on_20160804",
"EUDB    RU-Tks  2010    2014    TIER2   1   RU-Tks_processamento_completato_il_20160304_con_dataset_fino_al_2014_zip",
"EUDB    RU-Vrk  2008    2008    TIER2   1   RU-Vrk_processed_on_20160613_zip",
"EUDB    SD-Dem  2005    2009    TIER1   2   SD-Dem_ex20160721_proc20161024",
"EUDB    SE-St1  2012    2014    TIER2   1   SE-St1_processed_on_20160805",
"EUDB    SN-Dhr  2010    2013    TIER1   1   SN-Dhr_ex20160801_proc20161017",
"AMERIFLUX   US-AR1  2009    2012    TIER1   1   US-AR1_processed_on_20160803",
"AMERIFLUX   US-AR2  2009    2012    TIER1   1   US-AR2_processed_on_20160803",
"AMERIFLUX   US-ARb  2005    2006    TIER1   1   US-ARb_processed_on_20160714",
"AMERIFLUX   US-ARc  2005    2006    TIER1   1   US-ARc_processed_on_20160714",
"AMERIFLUX   US-ARM  2003    2012    TIER1   1   US-ARM_processed_on_20160804",
"AMERIFLUX   US-Atq  2003    2008    TIER2   1   US-Atq_processamento_completato_il_20160415_zip",
"AMERIFLUX   US-Blo  1997    2007    TIER1   1   US-Blo_processed_on_20160805",
"AMERIFLUX   US-Cop  2001    2007    TIER1   1   US-Cop-20160311-ready_processamento_completato_il_20160414_zip",
"AMERIFLUX   US-CRT  2011    2013    TIER2   1   US-CRT_processed_on_20160805",
"AMERIFLUX   US-GBT  1999    2006    TIER1   1   US-GBT-20160721-ready_processed_on_20160825",
"AMERIFLUX   US-GLE  2004    2014    TIER1   1   US-GLE_processed_on_20160719",
"AMERIFLUX   US-Goo  2002    2006    TIER2   1   US-Goo_processed_on_20160808",
"AMERIFLUX   US-Ha1  1991    2012    TIER1   1   US-Ha1_processamento_completato_il_20160219_con_dataset_fino_al_2012_zip",
"AMERIFLUX   US-IB2  2004    2011    TIER2   1   US-IB2_processed_on_20160808",
"AMERIFLUX   US-Ivo  2004    2007    TIER2   1   US-Ivo_processed_on_20160805",
"AMERIFLUX   US-KS1  2002    2002    TIER2   1   US-KS1_processed_on_20160803",
"AMERIFLUX   US-KS2  2003    2006    TIER1   1   US-KS2-20160323-ready_processamento_completato_il_20160414_zip",
"AMERIFLUX   US-Lin  2009    2010    TIER2   1   US-Lin_processed_on_20160808",
"AMERIFLUX   US-Los  2000    2014    TIER1   2   US-Los_processed_on_20160809",
"AMERIFLUX   US-LWW  1997    1998    TIER2   1   US-LWW-20160311-ready_processamento_completato_il_20160407_zip",
"AMERIFLUX   US-Me1  2004    2005    TIER1   1   US-Me1-20160323-ready_processamento_completato_il_20160414_zip",
"AMERIFLUX   US-Me2  2002    2014    TIER1   1   US-Me2_processamento_completato_il_20160330_zip",
"AMERIFLUX   US-Me3  2004    2009    TIER2   1   US-Me3_processed_on_20160816",
"AMERIFLUX   US-Me4  1996    2000    TIER2   1   US-Me4_processed_on_20160816",
"AMERIFLUX   US-Me5  2000    2002    TIER2   1   US-Me5_processed_on_20160816",
"AMERIFLUX   US-Me6  2010    2014    TIER1   2   US-Me6_processamento_completato_il_20160330_zip",
"AMERIFLUX   US-MMS  1999    2014    TIER1   1   US-MMS_processed_on_20160621",
"AMERIFLUX   US-Myb  2010    2014    TIER1   2   US-Myb_togliere_2015_processed_on_20160805",
"AMERIFLUX   US-Ne1  2001    2013    TIER1   1   US-Ne1_processed_on_20160809",
"AMERIFLUX   US-Ne2  2001    2013    TIER1   1   US-Ne2_processed_on_20160809",
"AMERIFLUX   US-Ne3  2001    2013    TIER1   1   US-Ne3_processed_on_20160809",
"AMERIFLUX   US-NR1  1998    2014    TIER1   1   US-NR1_processamento_completato_il_20160419_zip",
"AMERIFLUX   US-Oho  2004    2013    TIER2   1   US-Oho_processed_on_20160810",
"AMERIFLUX   US-ORv  2011    2011    TIER1   1   US-ORv_processed_on_20160714",
"AMERIFLUX   US-PFa  1995    2014    TIER1   1   US-PFa_processamento_completato_il_20160223_con_dataset_fino_al_2014_zip",
"AMERIFLUX   US-Prr  2010    2013    TIER1   1   US-Prr_processed_on_20160816",
"AMERIFLUX   US-Prr  2014    2014    TIER2   1   US-Prr_processed_on_20160816",
"AMERIFLUX   US-SRC  2008    2014    TIER2   1   US-SRC_processamento_completato_il_20160422_zip",
"AMERIFLUX   US-SRG  2008    2014    TIER1   1   US-SRG_processamento_completato_il_20160420_zip",
"AMERIFLUX   US-SRM  2004    2014    TIER1   1   US-SRM_processed_on_20160810",
"AMERIFLUX   US-Sta  2005    2009    TIER2   1   US-Sta_processamento_completato_il_20160419_zip",
"AMERIFLUX   US-Syv  2001    2014    TIER1   1   US-Syv_processed_on_20160810",
"AMERIFLUX   US-Ton  2001    2014    TIER1   1   US-Ton_processed_on_20160810",
"AMERIFLUX   US-Tw1  2012    2014    TIER1   1   US-Tw1_processamento_completato_il_20160419_zip",
"AMERIFLUX   US-Tw2  2012    2013    TIER1   1   US-Tw2-20160311-ready_processamento_completato_il_20160408_zip",
"AMERIFLUX   US-Tw3  2013    2014    TIER1   2   US-Tw3_processamento_completato_il_20160419_zip",
"AMERIFLUX   US-Tw4  2013    2014    TIER1   1   US-Tw4_processed_on_20160722",
"AMERIFLUX   US-Twt  2009    2014    TIER1   1   US-Twt_processamento_completato_il_20160421_zip",
"AMERIFLUX   US-UMB  2000    2014    TIER1   1   US-UMB_processamento_completato_il_20160201_con_dataset_fino_al_2014_zip",
"AMERIFLUX   US-UMd  2007    2014    TIER1   1   US-UMd_processed_on_20160810",
"AMERIFLUX   US-Var  2000    2014    TIER1   1   US-Var_processed_on_20160817",
"AMERIFLUX   US-WCr  1999    2014    TIER1   1   US-WCr_processed_on_20160811",
"AMERIFLUX   US-Whs  2007    2014    TIER1   1   US-Whs_processed_on_20160812",
"AMERIFLUX   US-Wi0  2002    2002    TIER1   1   US-Wi0_processamento_completato_il_20160419_zip",
"AMERIFLUX   US-Wi1  2003    2003    TIER2   1   US-Wi1_processed_on_20160801",
"AMERIFLUX   US-Wi2  2003    2003    TIER2   1   US-Wi2_processed_on_20160801",
"AMERIFLUX   US-Wi3  2002    2004    TIER1   1   US-Wi3_processamento_completato_il_20160419_zip",
"AMERIFLUX   US-Wi4  2002    2005    TIER1   1   US-Wi4_processamento_completato_il_20160419_zip",
"AMERIFLUX   US-Wi5  2004    2004    TIER2   1   US-Wi5_processed_on_20160801",
"AMERIFLUX   US-Wi6  2002    2003    TIER1   1   US-Wi6_processamento_completato_il_20160419_zip",
"AMERIFLUX   US-Wi7  2005    2005    TIER2   1   US-Wi7_processed_on_20160801",
"AMERIFLUX   US-Wi8  2002    2002    TIER2   1   US-Wi8_processed_on_20160816",
"AMERIFLUX   US-Wi9  2004    2005    TIER1   1   US-Wi9_processamento_completato_il_20160419_zip",
"AMERIFLUX   US-Wkg  2004    2014    TIER1   1   US-Wkg_processed_on_20160812",
"AMERIFLUX   US-WPT  2011    2013    TIER2   1   US-WPT_processed_on_20160810",
"EUDB    ZA-Kru  2000    2010    TIER1   1   ZA-Kru_processed_on_20160804",
"EUDB    ZA-Kru  2011    2013    TIER2   1   ZA-Kru_processed_on_20160804",
"EUDB    ZM-Mon  2000    2009    TIER1   2   ZM-Mon_processed_on_20160804",
]

SITES_HH = [
'AR-SLu', 'AR-Vir', 'AT-Neu', 'AU-Ade', 'AU-ASM', 'AU-Cpr', 'AU-Cum', 'AU-DaP',
'AU-DaS', 'AU-Dry', 'AU-Emr', 'AU-Fog', 'AU-Gin', 'AU-GWW', 'AU-How', 'AU-Lox',
'AU-RDF', 'AU-Rig', 'AU-Rob', 'AU-Stp', 'AU-TTE', 'AU-Wac', 'AU-Whr', 'AU-Wom',
'AU-Ync', 'BE-Bra', 'BE-Lon', 'BE-Vie', 'BR-Sa3', 'CA-Gro', 'CA-Man', 'CA-NS1',
'CA-NS2', 'CA-NS3', 'CA-NS4', 'CA-NS5', 'CA-NS6', 'CA-NS7', 'CA-Oas', 'CA-Obs',
'CA-Qfo', 'CA-SF1', 'CA-SF2', 'CA-SF3', 'CA-TP1', 'CA-TP2', 'CA-TP3', 'CA-TP4',
'CA-TPD', 'CG-Tch', 'CH-Cha', 'CH-Dav', 'CH-Fru', 'CH-Lae', 'CH-Oe1', 'CH-Oe2',
'CN-Cha', 'CN-Cng', 'CN-Dan', 'CN-Din', 'CN-Du2', 'CN-Du3', 'CN-Ha2', 'CN-HaM',
'CN-Qia', 'CN-Sw2', 'CZ-BK1', 'CZ-BK2', 'CZ-wet', 'DE-Akm', 'DE-Geb', 'DE-Gri',
'DE-Hai', 'DE-Kli', 'DE-Lkb', 'DE-Lnf', 'DE-Obe', 'DE-RuR', 'DE-RuS', 'DE-Seh',
'DE-SfN', 'DE-Spw', 'DE-Tha', 'DE-Zrk', 'DK-Eng', 'DK-Fou', 'DK-NuF', 'DK-Sor',
'DK-ZaF', 'DK-ZaH', 'ES-Amo', 'ES-LgS', 'ES-LJu', 'ES-Ln2', 'FI-Hyy', 'FI-Jok',
'FI-Let', 'FI-Lom', 'FI-Sod', 'FR-Fon', 'FR-Gri', 'FR-LBr', 'FR-Pue', 'GF-Guy',
'GH-Ank', 'IT-BCi', 'IT-CA1', 'IT-CA2', 'IT-CA3', 'IT-Col', 'IT-Cp2', 'IT-Cpz',
'IT-Isp', 'IT-La2', 'IT-Lav', 'IT-MBo', 'IT-Noe', 'IT-PT1', 'IT-Ren', 'IT-Ro1',
'IT-Ro2', 'IT-SR2', 'IT-SRo', 'IT-Tor', 'JP-MBF', 'JP-SMF', 'MY-PSO', 'NL-Hor',
'NL-Loo', 'NO-Adv', 'PA-SPn', 'PA-SPs', 'RU-Che', 'RU-Cok', 'RU-Fyo', 'RU-Ha1',
'RU-Sam', 'RU-SkP', 'RU-Tks', 'RU-Vrk', 'SD-Dem', 'SE-St1', 'SN-Dhr', 'US-AR1',
'US-AR2', 'US-ARb', 'US-ARc', 'US-ARM', 'US-Atq', 'US-Blo', 'US-CRT', 'US-GBT',
'US-GLE', 'US-Goo', 'US-IB2', 'US-Ivo', 'US-KS1', 'US-KS2', 'US-Lin', 'US-Los',
'US-LWW', 'US-Me1', 'US-Me2', 'US-Me3', 'US-Me4', 'US-Me5', 'US-Me6', 'US-Myb',
'US-NR1', 'US-Oho', 'US-ORv', 'US-Prr', 'US-SRC', 'US-SRG', 'US-SRM', 'US-Sta',
'US-Syv', 'US-Ton', 'US-Tw1', 'US-Tw2', 'US-Tw3', 'US-Tw4', 'US-Twt', 'US-UMd',
'US-Var', 'US-WCr', 'US-Whs', 'US-Wi0', 'US-Wi1', 'US-Wi2', 'US-Wi3', 'US-Wi4',
'US-Wi5', 'US-Wi6', 'US-Wi7', 'US-Wi8', 'US-Wi9', 'US-Wkg', 'US-WPT', 'ZA-Kru',
'ZM-Mon',
]

SITES_HR = [
'AU-Tum', 'BR-Sa1', 'NO-Blv', 'US-Cop', 'US-Ha1', 'US-MMS', 'US-Ne1', 'US-Ne2',
'US-Ne3', 'US-PFa', 'US-UMB',
]

SITES_RECINT = {s:'hh' for s in SITES_HH}
SITES_RECINT.update({s:'hr' for s in SITES_HR})

SITES_RECLEN_D = {
'AU-Rob': 1, 'DK-Fou': 1, 'ES-Ln2': 1, 'RU-Vrk': 1, 'US-KS1': 1,
'US-ORv': 1, 'US-Wi0': 1, 'US-Wi1': 1, 'US-Wi2': 1, 'US-Wi5': 1,
'US-Wi7': 1, 'US-Wi8': 1, 'AU-GWW': 2, 'AU-Lox': 2, 'CN-Dan': 2,
'CN-Du3': 2, 'DE-Zrk': 2, 'IT-Isp': 2, 'IT-SR2': 2, 'NO-Blv': 2,
'US-ARb': 2, 'US-ARc': 2, 'US-Lin': 2, 'US-LWW': 2, 'US-Me1': 2,
'US-Tw2': 2, 'US-Tw3': 2, 'US-Tw4': 2, 'US-Wi6': 2, 'US-Wi9': 2,
'AR-SLu': 3, 'AU-Ade': 3, 'AU-Cum': 3, 'AU-Emr': 3, 'AU-Fog': 3,
'AU-RDF': 3, 'AU-TTE': 3, 'AU-Ync': 3, 'CA-TPD': 3, 'CN-Cha': 3,
'CN-Din': 3, 'CN-Du2': 3, 'CN-Ha2': 3, 'CN-HaM': 3, 'CN-Qia': 3,
'CN-Sw2': 3, 'DE-SfN': 3, 'ES-LgS': 3, 'FI-Lom': 3, 'IT-Cp2': 3,
'IT-La2': 3, 'IT-PT1': 3, 'JP-MBF': 3, 'PA-SPn': 3, 'PA-SPs': 3,
'RU-Ha1': 3, 'RU-SkP': 3, 'SE-St1': 3, 'US-CRT': 3, 'US-Me5': 3,
'US-Tw1': 3, 'US-Wi3': 3, 'US-WPT': 3, 'AR-Vir': 4, 'AU-Gin': 4,
'AU-Rig': 4, 'AU-Wac': 4, 'AU-Whr': 4, 'CA-NS4': 4, 'CA-NS7': 4,
'CA-SF1': 4, 'CG-Tch': 4, 'CN-Cng': 4, 'DE-RuR': 4, 'DE-RuS': 4,
'DE-Seh': 4, 'DK-Eng': 4, 'DK-ZaF': 4, 'FI-Jok': 4, 'FI-Let': 4,
'GH-Ank': 4, 'IT-CA1': 4, 'IT-CA2': 4, 'IT-CA3': 4, 'NO-Adv': 4,
'RU-Che': 4, 'SN-Dhr': 4, 'US-AR1': 4, 'US-AR2': 4, 'US-Ivo': 4,
'US-KS2': 4, 'US-Wi4': 4, 'AU-ASM': 5, 'AU-Cpr': 5, 'AU-Wom': 5,
'BR-Sa3': 5, 'CA-NS1': 5, 'CA-NS2': 5, 'CA-NS3': 5, 'CA-NS5': 5,
'CA-NS6': 5, 'CA-SF2': 5, 'DE-Lkb': 5, 'DE-Spw': 5, 'JP-SMF': 5,
'RU-Tks': 5, 'SD-Dem': 5, 'US-Goo': 5, 'US-Me4': 5, 'US-Me6': 5,
'US-Myb': 5, 'US-Prr': 5, 'US-Sta': 5, 'CA-SF3': 6, 'CA-TP2': 6,
'DE-Akm': 6, 'ES-Amo': 6, 'US-Atq': 6, 'US-Me3': 6, 'US-Twt': 6,
'AU-DaP': 7, 'AU-DaS': 7, 'AU-Dry': 7, 'AU-Stp': 7, 'CH-Oe1': 7,
'DE-Obe': 7, 'DK-NuF': 7, 'IT-Tor': 7, 'MY-PSO': 7, 'US-Cop': 7,
'US-SRC': 7, 'US-SRG': 7, 'CA-Qfo': 8, 'NL-Hor': 8, 'US-GBT': 8,
'US-IB2': 8, 'US-UMd': 8, 'US-Whs': 8, 'CZ-BK2': 9, 'CZ-wet': 9,
'IT-Ro1': 9, 'BR-Sa1': 10, 'CH-Cha': 10, 'CH-Fru': 10, 'ES-LJu': 10,
'FR-Fon': 10, 'US-ARM': 10, 'US-Oho': 10, 'ZM-Mon': 10, 'AT-Neu': 11,
'BE-Lon': 11, 'CH-Lae': 11, 'CH-Oe2': 11, 'CZ-BK1': 11, 'DE-Gri': 11,
'DE-Kli': 11, 'DE-Lnf': 11, 'FR-Gri': 11, 'GF-Guy': 11, 'IT-BCi': 11,
'IT-MBo': 11, 'IT-Noe': 11, 'IT-Ro2': 11, 'US-Blo': 11, 'US-GLE': 11,
'US-SRM': 11, 'US-Wkg': 11, 'CA-Gro': 12, 'IT-Lav': 12, 'RU-Cok': 12,
'CA-TP1': 13, 'CA-TP3': 13, 'CA-TP4': 13, 'DE-Hai': 13, 'FR-LBr': 13,
'IT-Cpz': 13, 'RU-Sam': 13, 'US-Me2': 13, 'US-Ne1': 13, 'US-Ne2': 13,
'US-Ne3': 13, 'AU-How': 14, 'AU-Tum': 14, 'CA-Obs': 14, 'DE-Geb': 14,
'FI-Sod': 14, 'IT-SRo': 14, 'US-Syv': 14, 'US-Ton': 14, 'ZA-Kru': 14,
'CA-Man': 15, 'CA-Oas': 15, 'DK-ZaH': 15, 'FR-Pue': 15, 'US-Los': 15,
'US-UMB': 15, 'US-Var': 15, 'IT-Ren': 16, 'US-MMS': 16, 'US-WCr': 16,
'RU-Fyo': 17, 'US-NR1': 17, 'CH-Dav': 18, 'BE-Bra': 19, 'BE-Vie': 19,
'DE-Tha': 19, 'DK-Sor': 19, 'FI-Hyy': 19, 'IT-Col': 19, 'NL-Loo': 19,
'US-PFa': 20, 'US-Ha1': 22,
}

MACHINES = ['olaf1', 'olaf2', 'olaf3', 'rocky1', 'rocky2', 'rocky3',
            'rocky4', 'rocky5', 'dash1', 'dash2', 'dash3', 'dash4',
            'dash5', 'polly1', 'polly2', 'polly3', 'polly4', 'coors1',
            'coors2', 'coors3', 'coors4', 'doright1', 'doright2',
            'doright3', 'doright4', 'doright5', ]

### parse site information
SITES_D = {}
SITES_FOLDERS_D = {}
for e in SITES_TIERS_FOLDERS:
    db, siteid, fy, ly, tier, version, sitedir = e.strip().split()
    if tier.strip().upper() not in ['TIER1', 'TIER2']:
        msg = "Unknown TIER '{t}' for site {s} ({f}-{l})".format(t=tier, s=siteid, f=fy, l=ly)
        log.error(msg)
        raise ONEFluxError(msg)

    # sites-tiers
    if SITES_D.has_key(siteid):
        SITES_D[siteid][tier].append((fy, ly))
        SITES_D[siteid]['FY'] = min(SITES_D[siteid]['FY'], fy)
        SITES_D[siteid]['LY'] = max(SITES_D[siteid]['LY'], ly)
        if SITES_D[siteid]['version'] != version:
            log.error("Versions differ for different tiers for site {s} ({v1} <> {v2})".format(s=siteid, v1=SITES_D[siteid]['version'], v2=version))
    else:
        SITES_D[siteid] = {}
        SITES_D[siteid]['TIER1'] = []
        SITES_D[siteid]['TIER2'] = []
        SITES_D[siteid]['version'] = version
        SITES_D[siteid][tier].append((fy, ly))
        SITES_D[siteid]['FY'] = fy
        SITES_D[siteid]['LY'] = ly
        SITES_D[siteid]['RECLEN'] = SITES_RECLEN_D[siteid]
        SITES_D[siteid]['RECINT'] = SITES_RECINT[siteid]
        SITES_D[siteid]['SITEDIR'] = sitedir


    # sites folders
    if SITES_FOLDERS_D.has_key(siteid):
        if SITES_FOLDERS_D[siteid] != sitedir:
            msg = "Multiple folders used for site {s}: {f1} and {f2}".format(s=siteid, f1=SITES_FOLDERS_D[siteid], f2=sitedir)
            log.critical(msg)
            raise ONEFluxError(msg)
    else:
        SITES_FOLDERS_D[siteid] = sitedir

log.info('Adding machines to lists of sites: {m}'.format(m=MACHINES))
SITE_LISTS.update({m:[] for m in MACHINES})
SITES_BY_RECLEN = [s for _, s in sorted([(v, k) for k, v in SITES_RECLEN_D.items()])]

for i in range(len(SITES_BY_RECLEN)):
    machine_id = MACHINES[i % len(MACHINES)]
    SITE_LISTS[machine_id].append(SITES_BY_RECLEN[i])


if __name__ == '__main__':
    sys.exit("ERROR: cannot run independently")
