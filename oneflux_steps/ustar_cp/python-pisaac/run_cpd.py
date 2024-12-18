# standard modules
import datetime
import time
import glob
import os
import warnings
# 3rd party modules
import numpy
import xlwt
# local modules
from cpdBootstrapUStarTh4Season20100901 import cpdBootstrapUStarTh4Season20100901
from cpdAssignUStarTh20100901 import cpdAssignUStarTh20100901

# PRI really hates to do this but can find no better way to suppress multiple
# RuntimeWarnings from Numpy except kludgy inline code hacks.
# PRI suggests commenting out this line when developing and testing and ony
# leaving it in for production.
# The whole thing needs to be done with masked arrays or pandas.
warnings.filterwarnings("ignore", category=RuntimeWarning)

exitcode = 0
error_str = ""
#input_folder = "/home/peter/Python/cpd/sites/AU-Fog/input/"
#output_folder = "/home/peter/Python/cpd/sites/AU-Fog/output/"
input_folder = "/home/peter/Python/cpd/comparisons/input/"
output_folder = "/home/peter/Python/cpd/comparisons/output/"
# get a list of files in the input folder
d = sorted(glob.glob(os.path.join(input_folder, "*_qca_ustar_*.csv")))
print str(len(d)) + " files found"
for file_number in range(len(d)):
    print "Processing ", d[file_number]
    with open(d[file_number]) as f:
        content = f.readlines()
    content = [l.strip() for l in content]
    # get the site metadata
    metadata = {}
    line_number = 0
    while content[line_number][0:5] != "notes":
        line = content[line_number]
        idx = line.index(",")
        metadata[line[:idx]] = line[idx+1:]
        line_number = line_number + 1
    # get the site notes
    notes = {}
    while content[line_number][0:5] == "notes":
        notes[line_number] = content[line_number]
        line_number = line_number + 1
    # read the rest of the data
    all_nan = False
    header = content[line_number].split(",")
    data = numpy.genfromtxt(content[line_number:], delimiter=",", names=True,
                            autostrip=True, dtype=float)
    for label in header:
        data[label] = numpy.where(data[label] == -9999, numpy.nan, data[label])
        all_nan = numpy.all(numpy.isnan(data[label]))
    # check to see if 1 or more inputs are all NaNs
    if all_nan:
        continue
    # generate time stamp as decimal day of year
    # NOTE: This assumes a record for every time step
    nrPerDay = numpy.mod(len(data["USTAR"]), 365)
    if nrPerDay == 0:
        nrPerDay = numpy.mod(len(data["USTAR"]), 364)
    start = 1 + float(1)/float(nrPerDay)
    stop = float(len(data["USTAR"]))/float(nrPerDay) + 1
    t = numpy.linspace(start, stop, len(data["USTAR"]))
    # day/night indicator
    fNight = numpy.where(data["SW_IN"] < 5, 1, 0)

    d_path, d_name = os.path.split(d[file_number])
    cSiteYr = d_name.replace(".txt", "")
    cSiteYr = cSiteYr.replace("_ut", "_barr")
    nBoot = 10
    fPlot = 0
    t0 = time.time()
    print "Calling cpdBootstrapUStarTh4Season20100901"
    Cp2, Stats2, Cp3, Stats3 = cpdBootstrapUStarTh4Season20100901(t, data["NEE"], data["USTAR"],
                                                                  data["TA"], fNight,
                                                                  fPlot, cSiteYr, nBoot)
    print "cpdBootstrapUStarTh4Season20100901 took " + str(time.time() - t0)
    print "Calling cpdAssignUStarTh201009"
    Cp, n, tW, CpW, cMode, cFailure, fSelect, sSine, FracSig, FracModeD, FracSelect = \
        cpdAssignUStarTh20100901(Stats2,fPlot,cSiteYr)
    print "This site took " + str(time.time() - t0)

    if len(cFailure) == 0:
        cSiteYr = cSiteYr.replace(".csv", "")
        site_str = metadata["site"]
        year_str = metadata["year"]
        output_name = site_str + "_uscp_" + year_str + "_py.txt"
        output_file = os.path.join(output_folder, output_name)
        with open(output_file, "w") as f:
            if numpy.isscalar(Cp):
                f.write(str(Cp) + "\n")
            else:
                for i in range(len(Cp)):
                    f.write(str(Cp[i]) + "\n")
            f.write("\n")
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            line = ";processed with ustar_cpd 1.0 (Python) on " + now + "\n"
            f.write(line)
            for k in notes.keys():
                line = notes[k]
                line = line.replace("notes,", ";")
                line = line + "\n"
                f.write(line)
    else:
        print "An error occurred processing file ", d[file_number]
        print cFailure
        exitcode = 1
    print "Finished processing ", d[file_number]

print "All done"
