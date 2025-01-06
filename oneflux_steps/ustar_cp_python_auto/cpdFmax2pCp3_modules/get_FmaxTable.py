# Generated with SMOP  0.41-beta
from libsmop import *
# oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3_modules/get_FmaxTable.m


@function
def get_FmaxTable():
    globals().update(load_all_vars())

    # get_FmaxTable returns the critical F-max values.
    FmaxTable = matlabarray(
        [
            [11.646, 15.559, 28.412],
            [9.651, 11.948, 18.043],
            [9.379, 11.396, 16.249],
            [9.261, 11.148, 15.75],
            [9.269, 11.068, 15.237],
            [9.296, 11.072, 15.252],
            [9.296, 11.059, 14.985],
            [9.341, 11.072, 15.013],
            [9.397, 11.08, 14.891],
            [9.398, 11.085, 14.874],
            [9.506, 11.127, 14.828],
            [9.694, 11.208, 14.898],
            [9.691, 11.31, 14.975],
            [9.79, 11.406, 14.998],
            [9.794, 11.392, 15.044],
            [9.84, 11.416, 14.98],
            [9.872, 11.474, 15.072],
            [9.929, 11.537, 15.115],
            [9.955, 11.552, 15.086],
            [9.995, 11.549, 15.164],
            [10.102, 11.673, 15.292],
            [10.169, 11.749, 15.154],
            [10.478, 12.064, 15.519],
        ]
    )
    # oneflux_steps/ustar_cp_refactor_wip/cpdFmax2pCp3_modules/get_FmaxTable.m:3
    return FmaxTable


if __name__ == "__main__":
    pass
