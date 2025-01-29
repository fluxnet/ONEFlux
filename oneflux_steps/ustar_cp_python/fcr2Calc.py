import numpy as np
from oneflux_steps.ustar_cp_python.utils import squeeze

def fcr2Calc(y=None, yHat=None):
    """
    Calculate the coefficient of determination (R^2) for the given observed and predicted values.

    Parameters:
    y (array-like): Observed values.
    yHat (array-like): Predicted values.

    Returns:
    float: The coefficient of determination (R^2), which indicates the proportion of the variance in the dependent variable that is predictable from the independent variable(s).

    Notes:
    - SSreg (Sum of Squares of the regression) is calculated as the sum of the squared differences between the predicted values and the mean of the observed values.
    - SStotal (Total Sum of Squares) is calculated as the sum of the squared differences between the observed values and the mean of the observed values.
    - RMSE (Root Mean Square Error) is calculated as the sum of the squared differences between the predicted values and the observed values.
    - R^2 is then calculated as the ratio of SSreg to SStotal.

    Example:
    >>> y = [3, -0.5, 2, 7]
    >>> yHat = [2.5, 0.0, 2, 8]
    >>> fcr2Calc(y, yHat)
    1.214132762312634
    """
    n = len(y)

    # Calculate the mean of the observed values.
    ym = np.mean(squeeze(np.asarray(y)), axis=0)
    # SSreg ((explained) Sum of Squares of the regression) 
    SSreg = np.sum((yHat - ym) ** 2)
    # SStotal (Total Sum of Squares)
    SStotal = np.sum((y - ym) ** 2)

    # RMSE (Root Mean Square Error)
    # TODO: can be remove as it is uunused
    rmse = np.sum((yHat - y) ** 2)

    # Calculate the coefficient of determination
    r2 = SSreg / SStotal
    return r2
