'''
oneflux.metadata

For license information:
see LICENSE file or headers in oneflux.__init__.py

Metadata handling functions for ONEFlux

@author: Carlo Trotta
@contact: trottacarlo@unitus.it
@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2025-10-30
'''


LICENSE_FILENAME = 'DATA_POLICY_LICENSE_AND_INSTRUCTIONS.txt'
LICENSE = '''**** DATA POLICY, LICENSE, AND INSTRUCTIONS FOR ATTRIBUTION ****

License document version 20251205

The FLUXNET data product is shared under the CC-BY-4.0 license (Creative Commons by Attribution 4.0 International: https://creativecommons.org/licenses/by/4.0/). The CC-BY-4.0 license requires that attribution be given with every use. With correct attribution, the data user is free to Share (copy and redistribute the material in any medium or format) and/or Adapt (remix, transform, and build upon the material) for any purpose.

Attribution of FLUXNET data products requires inclusion of a citation for each site and acknowledgments. The site's citation guidelines and network-specific acknowledgments are provided in this DATA_USE_LICENSE_AND_INSTRUCTIONS document that is included in each site's FLUXNET data zip file. 
 
If FLUXNET data products from multiple networks are used, the attribution requirements for each of the included networks must be followed. Use the product source-network code (the first letters of the FLUXNET zip filename or the PRODUCT_SOURCE_NETWORK in the ancillary BIF file), to determine the lettered sub-items that are additionally required to the global requirements listed below.

---- REQUIRED ATTRIBUTION ----

Include the citation for each site's FLUXNET data product in your paper or project. For journal articles, the citation must appear in the reference section or other section that supports citation tracking (e.g., not supplementary material). The citation is provided in the metadata available during the data download process, and must include the PID or DOI. Citations for the data can also be retrieved using the network-specific procedures at the end of this document.
Include the following text in the acknowledgment, for any use of FLUXNET data: FLUXNET data products were produced and harmonized by eddy covariance regional networks and data processing centers, including AmeriFlux, ChinaFlux, European Fluxes Database, ICOS, JapanFlux, KoFlux, OzFlux, SAEON, and TERN. These products also include a modified version of ERA5 hourly data provided by the Copernicus Climate Change Service.
When AmeriFlux (AMF) data are used, add the text: "Funding for the AmeriFlux data service was provided by the U.S. Department of Energy Office of Science." 
When ChinaFlux (CNF) data are used, add the text: "ChinaFlux data are from the National ecosystem science data center https://www.nesdc.org.cn" and add in the references the paper Yu et al (2006) https://doi.org/10.1016/j.agrformet.2006.02.011
When JapanFlux (JPF) data are used, add in the references the paper Ueyama et al (2005) https://doi.org/10.5194/essd-17-3807-2025
When OzFlux (OZF) data are used, add the text: "OzFlux data are from the OzFlux Data Portal https://data.ozflux.org.au/home.jspx" and add in the references to the papers Beringer et al (2016) https://doi.org/10.5194/bg-13-5895-2016 and Isaac et al (2017) https://doi.org/10.5194/bg-14-2903-2017
When TERN (TERN) data are used, add the text: "TERN data are from the TERN Data Discovery Portal https://portal.tern.org.au/browse/theme" and add in the references to the papers Beringer et al (2016) https://doi.org/10.5194/bg-13-5895-2016 and Isaac et al (2017) https://doi.org/10.5194/bg-14-2903-2017
If there is a Data Availability section in your paper, include the following in that section (in addition to the citation in a reference section): "The FLUXNET data products used in this work were downloaded from [SOURCE] on XX Month YYYY".
[SOURCE] is the interface or tool used to access the data. It can be the AmeriFlux, TERN or ICOS data portal, the FLUXNET User Interface for the Shuttle, or the Shuttle code directly. 
For example, "The FLUXNET data products used in this study were downloaded from the ICOS Carbon Portal (https://data.icos-cp.eu/portal/) on 1 January 2026".

The required data citation and PIs' name and email addresses for the downloaded sites are provided to the data user with the data download process (e.g., the shuttle metadata output). In case needed, these information can be retrieved also:
For sites processed by AmeriFlux (AMF), via each site's AmeriFlux Site Info page or can be generated for multiple sites using the "Site Set" feature (See Site Search: https://ameriflux.lbl.gov/sites/site-search/).
For sites processed by ICOS and European Fluxes Database (CNF, EUF, ICOS, JPF, KOF, SAEON), via https://data.icos-cp.eu/portal/ selecting FLUXNET as project or through the SPARQL endpoint at https://meta.icos-cp.eu/sparqlclient
For sites processed by TERN (OZF, TERN), via https://data.ozflux.org.au/pub/listPubCollections.jspx, select the collection for the site and copy the text under the Citation Information heading.

---- RECOMMENDED ATTRIBUTION ----

It is recommended to include the citation for the FLUXNET processing paper: Pastorello, G., Trotta, C., Canfora, E. et al. The FLUXNET2015 dataset and the ONEFlux processing pipeline for eddy covariance data. Sci Data 7, 225 (2020). https://doi.org/10.1038/s41597-020-0534-3.


---- ADDITIONAL SUGGESTIONS ----
Collaboration with data providers (PIs, site teams, data processing teams, etc.) during the preparation of a manuscript or other research product is not required under the CC-BY-4.0 license. However, such collaboration is strongly encouraged, as it can help prevent potential misinterpretations or other technical inconsistencies and is generally appreciated by the data providers.

The JapanFlux  input data used for the FLUXNET product are available at https://ads.nipr.ac.jp/japan-flux2024/ with site specific DOIs that can be cited.



---- ADDITIONAL DATA POLICY RESOURCES ----

AmeriFlux (AMF) data generated and published by the AmeriFlux network: https://ameriflux.lbl.gov/data/data-policy/ (see the AmeriFlux CC-BY-4.0 license section). 
ICOS data generated and published: https://www.icos-cp.eu/how-to-cite
JapanFlux data generated and published: https://ads.nipr.ac.jp/japan-flux2024/
TERN data generated and published: https://www.tern.org.au/terms-of-use/
The always up-to-date FLUXNET data license and attribution guidelines are also available at data.fluxnet.org.

---- CONTACTS ----
For any question about proper data attribution please contact support@fluxnet.org.
'''


README_FILENAME = 'README.txt'
README = '''**** README FILE - GENERAL INFORMATION ****

FLUXNET DATA PRODUCT CONTENT
The FLUXNET data product generated by ONEFlux is an international standard used by different eddy covariance networks globally. It is a compressed archive (zip) that includes a set of files:

_README_: this file, with general information about the data product

_DATA_POLICY_LICENSE_AND_INSTRUCTIONS_: The FLUXNET data are shared under a CC-BY-4.0 data use license. See this file for details of the data license and attribution requirements when data are used

Five files, with different time aggregations, containing the continuous data (flux and meteorological). The files (csv following the FP Standard format) have this name structure:

       [N]_[CC-###]_FLUXNET_FLUXMET_[T]_[YS]-[YE]_[V]_[R].csv

where:
[N] = code identifying the source network** 
[CC-###] = the FLUXNET site code
[T] = the time resolution, with options HH for hourly or half-hourly, DD for daily, WW for weekly, MM for monthly, and YY for yearly
[YS]-[YE] = the start and end years of the measurements
[V] = the version of ONEFlux used*
[R] = the data release version

Five files, with different time aggregations, containing the continuous variables definitions, units and information. The files (BIF Standard format) have this name structure:

                   [N]_[CC-###]_FLUXNET_BIFVARINFO_[T]_[YS]-[YE]_[V]_[R].csv

where:
[N] = code identifying the source network** 
[CC-###] = the FLUXNET site code
[T] = the time resolution, with options HH for hourly or half-hourly, DD for daily, WW for weekly, MM for monthly, and YY for yearly
[YS]-[YE] = the start and end years of the measurements
[V] = the version of ONEFlux used*
[R] = the data release version

Five files, with different time aggregations, containing the ERA meteorological data downscaled at the level of the site. The files (csv following the FP Standard format) have this name structure:

       [N]_[CC-###]_FLUXNET_ERA5_[T]_[YS]-[YE]_[V]_[R].csv

where:
[N] = code identifying the source network** 
[CC-###] = the FLUXNET site code
[T] = the time resolution, with options HH for hourly or half-hourly, DD for daily, WW for weekly, MM for monthly and YY for yearly
[YS]-[YE] = the start and end years of the measurements
[V] = the version of ONEFlux used*
[R] = the data release version

One file with all the metadata and ancillary data of the site (BIF Standard format) with name structure: 

       [N]_[CC-###]_FLUXNET_BIF_[YS]-[YE]_[V]_[R].csv

where:
[N] = code identifying the source network** 
[CC-###] = the FLUXNET site code
[YS]-[YE] = the start and end years of the measurements
[V] = the version of ONEFlux used*
[R] = the data release version


* The version of ONEFlux included in the filename only contains the major and minor designation (e.g., v1.2) of the full code version (e.g., v1.2.1). The full ONEFlux code version can be found in the BIF metadata files.

** Regional network that prepares and manages in a coordinated and centralized way the flux/met data and the metadata for ONEFlux processing. This network is a contact for questions about the site. Explanations of the codes are available in the BADM variable PRODUCT_SOURCE_NETWORK, see below.

CONTINUOUS DATA FORMAT AND PROCESSING
The continuous data are collected by each site PI and team and prepared by Regional Networks before the final processing using the ONEFlux pipeline (https://github.com/fluxnet/ONEFlux). The processing and the data format are described in Pastorello et al. 2020 and further developments of the code in the ONEFlux GitHub repository.
The data are in ASCII format, comma delimited, with first row as header. Missing data are indicated as -9999 and time is expressed in local solar time (without DST). Metadata about the measurements are reported in the VAR_INFO BIF files.

BIF DATA FORMAT
The BIF (BADM Interchange Format, where BADM is Biological Ancillary Disturbance and Metadata) is a standard ASCII Data format to report non continuous data (ancillary data, metadata etc.). It is described in the Table SM8 (Supplementary material) of Pastorello et al. 2020. The description of the variables is available, always updated, on the https://fluxnet.org/ website and the FLUXNET github (https://github.com/fluxnet/BIF_BADM)
An online tool to convert BIF format in tables is available at https://tinyurl.com/BIFconverter (needs Google Drive to run)

CONTACTS
For any question about the data processing and format please contact us via email at  support@fluxnet.org 



Pastorello, G., Trotta, C., Canfora, E. et al. The FLUXNET2015 dataset and the ONEFlux processing pipeline for eddy covariance data. Sci Data 7, 225 (2020). https://doi.org/10.1038/s41597-020-0534-3
'''
