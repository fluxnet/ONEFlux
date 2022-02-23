'''
oneflux.configs_local

For license information:
see LICENSE file or headers in oneflux.__init__.py 

Pipeline optional configuration parameters

@author: Gilberto Z. Pastorello
@contact: gzpastorello@lbl.gov
@date: 2021-09-01
'''
import sys

# # Configs for ONEFlux running for: FLUXNET sites, creating FLUXNET2015 data product, using ERA-Interim downscaling
# MODE_ISSUER = 'FLX'
# MODE_PRODUCT = 'FLUXNET2015'
# MODE_ERA = 'ERAI'
# ERA_FIRST_YEAR = 1989
# ERA_LAST_YEAR = 2014

# Configs for ONEFlux running for: FLUXNET sites, creating FLUXNET data product, using ERA-5 downscaling
MODE_ISSUER = 'FLX'
MODE_PRODUCT = 'FLUXNET'
MODE_ERA = 'ERA5'
ERA_FIRST_YEAR = 1981
ERA_LAST_YEAR = 2020


if __name__ == '__main__':
    sys.exit("ERROR: cannot run independently")
