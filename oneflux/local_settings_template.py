'''
oneflux.configs_local

For license information:
see LICENSE file or headers in oneflux.__init__.py 

Pipeline optional configuration parameters.

***N.B.
To use this file, make a copy in local version of repository
(same directory) and rename to local_settings.py
If local_settings.py is not found, configs hardcoded will be adopted.
Note that local_settings.py should not be added to shared repositories,
and is listed in .gitignore

@author: Gilberto Z. Pastorello
@contact: gzpastorello@lbl.gov
@date: 2021-09-01
'''
import sys

### Configs for ONEFlux runs
# MODE_ISSUER: issuer of data product, 3-characters; examples include (FLX: FLUXNET, AMF: AmeriFlux, ETC: ICOS-ETC, EUF: European DB, OZF: OzFlux)
# MODE_PRODUCT: data product being generated; currently supported only FLUXNET2015 (historical) and FLUXNET (current product)
# MODE_ERA: ERA data product used for downscaling; currently supported only ERAI (ERA-Interim, used for FLUXNET2015) and ERA5 (ERA version 5)
# ERA_FIRST_YEAR: default value for first year of ERA downscaled data; for ERAI use 1989, ERA5 use 1981
# ERA_LAST_YEAR: default value for first year of ERA downscaled data; for ERAI for FLUXNET2015 use 2014, ERA5 include 2020, 2021, etc.

# # Configs for ONEFlux running for: FLUXNET sites, creating FLUXNET2015 data product, using ERA-Interim downscaling
# MODE_ISSUER = 'FLX'
# MODE_PRODUCT = 'FLUXNET2015'
# MODE_ERA = 'ERAI'
# ERA_FIRST_YEAR = 1989
# ERA_LAST_YEAR = 2014

# # Configs for ONEFlux running for: AmeriFlux sites, creating FLUXNET data product, using ERA-5 downscaling
# MODE_ISSUER = 'AMF'
# MODE_PRODUCT = 'FLUXNET'
# MODE_ERA = 'ERA5'
# ERA_FIRST_YEAR = 1981
# ERA_LAST_YEAR = 2021

# # Configs for ONEFlux running for: EUDB sites, creating FLUXNET data product, using ERA-5 downscaling
# MODE_ISSUER = 'EUF'
# MODE_PRODUCT = 'FLUXNET'
# MODE_ERA = 'ERA5'
# ERA_FIRST_YEAR = 1981
# ERA_LAST_YEAR = 2021

# Configs for ONEFlux running for: FLUXNET sites, creating FLUXNET data product, using ERA-5 downscaling
MODE_ISSUER = 'FLX'
MODE_PRODUCT = 'FLUXNET'
MODE_ERA = 'ERA5'
ERA_FIRST_YEAR = 1981
ERA_LAST_YEAR = 2021


if __name__ == '__main__':
    sys.exit("ERROR: cannot run independently")
