import oneflux.partition.nighttime
import oneflux.partition.library # optimisation related functions
import oneflux.partition.ecogeo


# LIBRARY
# looks like a good candidate for unit testing - lots of maths functions:
# get_first_last_ts
# cov2cor
# root_mean_sq_error
# least_squares () - calls scipy function 
# check_parameters (checks values within given threshold)

# loading data function:
# load outputs

# Less easy:
# create_data_structures - very long function
#  nlinlts1 (non-linear least-squares driver function)

# function is used in daytime at present - so ignore for now
# array consisting of 6 elements
def test_check_parameters():
    from oneflux.partition.library import check_parameter
   
    #  
    p1 = [0, 0, 0, 50, 0, 0]
    
    p2 = [0.2199999, 250, 0, 0, 0, 0]

# flux partition in nighttime.py is a huge function (250+ lines)

def test_load_output():
    from oneflux.partition.library import load_output
    pass

def test_compu():
    pass

def test_get_first_last_ts():
    pass


# partitioning_nt -> flux_partition -> nlinlts -> 