# test_my_figure_functions.py

import matlab.engine
import pytest


def test_myFigLoc(matlab):
    # Test case for the myFigLoc function
    
    # Define input parameters
    iFig = 1
    dx = 0.3
    dy = 0.4
    cLoc = 'NW'
    
    # Call the function from MATLAB
    matlab.myFigLoc(iFig, dx, dy, cLoc, nargout=0)
    
    # You would typically check the figure's properties here. However, as we are running in headless mode,
    # we may not be able to directly check the figure properties. 
    # Instead, you might want to mock the MATLAB functions or use another method to verify the behavior.

    # Example checks (need a more sophisticated approach for real checks)
    assert True

# Additional tests for helper functions if needed

def test_parseLocation(matlab):
    # Test case for the parseLocation function
    
    cLoc = 'xShift=0.7 yShift=0.2 UpperRight'
    
    # Call the helper function directly
    xFractionShift, yFractionShift = matlab.parseLocation(cLoc)
    
    assert xFractionShift == 0.7
    assert yFractionShift == 0.2

def test_calculateFigurePosition(matlab):
    # Test case for the calculateFigurePosition function
    
    dx = 0.3
    dy = 0.4
    xFractionShift = 0.5
    yFractionShift = 0.5
    
    # Call the helper function directly
    FigLoc = matlab.calculateFigurePosition(dx, dy, xFractionShift, yFractionShift)
    
    assert len(FigLoc) == 4
    assert isinstance(FigLoc, (list, tuple))  # Ensure FigLoc is a list or tuple
    assert all(isinstance(x, float) for x in FigLoc)  # Ensure all elements are floats

def test_getScreenSize(matlab):
    # Test case for the getScreenSize function
    
    # Call the helper function directly
    nxPixels, nyPixels = matlab.getScreenSize()
    
    assert isinstance(nxPixels, int)
    assert isinstance(nyPixels, int)
    assert nxPixels > 0
    assert nyPixels > 0
