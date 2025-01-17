"""
This module contains pytest fixtures and utility functions to set up the test environment,
handle MATLAB engine interactions, and process text files for comparison in unit tests.

Contents:
    Fixtures:
        test_engine
        setup_folders
        find_text_file
        extract_section_between_keywords
        load_json
    Helper_functions:
        process_std_out
        compare_text_blocks
        to_matlab_type
        read_csv_with_csv_module
        read_file
        parse_testcase
"""

import pytest
import os
import matlab.engine
import shutil
import glob
import json
import io
import atexit
import numpy as np
from matlab.engine.matlabengine import MatlabFunc

from oneflux_steps.ustar_cp_python.utils import transpose

class MFWrapper:
    def __init__(self, func):
        self.func = func
        self.out = io.StringIO()
        self.err = io.StringIO()
        name = func._name
        # make matlab stdout and stderr printed at the end of pytest
        atexit.register(lambda: (s := self.out.getvalue()) and print(f"{name} stdout:\n{s}"))
        atexit.register(lambda: (s := self.err.getvalue()) and print(f"{name} stderr:\n{s}"))
        
    def __call__(self, *args, jsonencode=(), jsondecode=(), **kwargs):
        """
        Call the wrapped function with optional JSON encoding/decoding to handle the issue that non-scalar structs (arrays of structs) cannot be returned from MATLAB functions to Python.
        Args:
            *args: Positional arguments to pass to the wrapped function.
            jsonencode (tuple, optional): Indices of output arguments to JSON encode (into string) before the matlab function returns.
            jsondecode (tuple, optional): Indices of input arguments to JSON decode (from string) at the beginning of the matlab function.
            **kwargs: Keyword arguments to pass to the wrapped function.
        Returns:
            The result of the wrapped function, with specified outputs JSON decoded if necessary.
        """
        args = list(args)
        if jsonencode:
            args.append(['jsonencode'] + [i+1 for i in jsonencode])
        if jsondecode:
            for i in jsondecode:
                args[i] = json.dumps(args[i])
            args.append(['jsondecode'] + [i+1 for i in jsondecode])
        out = kwargs.pop('stdout', self.out)
        err = kwargs.pop('stderr', self.err)
        ret = self.func(*args, **kwargs, stdout=out, stderr=err)
        if jsonencode:
            nargout = kwargs.get('nargout', 1)
            if nargout <= 1:
                ret = [ret]
            else:
                ret = list(ret)
            for j in jsonencode:
                ret[j] = json.loads(ret[j], object_hook=none2nan)
            if nargout <= 1:
                ret = ret[0]
        return ret

def mf_factory(cls, *args, **kwargs):
    f = object.__new__(MatlabFunc)
    f.__init__(*args, **kwargs)
    return MFWrapper(f)
MatlabFunc.__new__ = mf_factory

# from oneflux_steps.ustar_cp_py.libsmop import matlabarray, struct
from abc import ABC, abstractmethod
import warnings

import oneflux_steps.ustar_cp_python.utils

# Python version imported here
from oneflux_steps.ustar_cp_python import *
from oneflux_steps.ustar_cp_python.cpdFmax2pCp3 import *
from oneflux_steps.ustar_cp_python.utilities import *
from oneflux_steps.ustar_cp_python.cpd_evaluate_functions import *

def pytest_addoption(parser):
    parser.addoption("--language", action="store", default="matlab")

@pytest.fixture(scope="session")
def language(pytestconfig):
    return pytestconfig.getoption("language")

# Specification of a `TestEngine`
class TestEngine(ABC):
    @abstractmethod
    def _repr_pretty_(self, *args):
        """This placeholder can stay as is; it enables Hypothesis to work with this
        runner as a fixture"""
        return "Test Engine"

    @abstractmethod
    def convert(self, x, fromFile=False):
        """Convert the input to a type compatible with this engine. Can just be identity
        if the runner is Python"""
        return np.array(x)

    @abstractmethod
    def unconvert(self, x):
        """Convert input back from the type compatible with this engine."""
        return np

    @abstractmethod
    def equal(self, x, y) -> bool:
        """Compare two values for equality in the representation used by this engine"""
        pass

# Python TestEngine
class PythonEngine(TestEngine):
    def _repr_pretty_(self, *args):
        return "Python Test Engine"

    def convert(self, x, index=False, fromFile=False):
        """Convert input to a compatible type."""
        if x is None:
            raise ValueError("Input cannot be None")
        if isinstance(x, list):
            # Transpose to capture MATLAB data layout
            # when the data has been serialised from MATLAB
            # to a file
            if fromFile:
              return transpose(np.array(x))
            else:
              return np.array(x)
              
        elif isinstance(x, tuple):
            return tuple([self.convert(xi) for xi in x])
        else:
            return x
        
    def unconvert(self, x):
        """Convert input back to the original type."""
        return x

    def equal(self, x, y) -> bool:
        """Enhanced equality check for MATLAB arrays."""
        if x is None or y is None:
            raise ValueError("Comparison values cannot be None")
        if isinstance(x, float) or isinstance(y, float):
            return np.isclose(x, y, equal_nan=True)
        elif isinstance(x, np.ndarray) and isinstance(y, np.ndarray):
            return np.allclose(x, y, equal_nan=True)
        elif (isinstance(x, list) and isinstance(y, list)) or (isinstance(x, tuple) and isinstance(y, tuple)):
            return all(self.equal(xi, yi) for xi, yi in zip(x, y))
        else:
            return x == y
    
    def __getattribute__(self, name):
        if name in ["convert", "unconvert", "equal", "_repr_pretty_"]:
            return object.__getattribute__(self, name)

        def newfunc(*args, **kwargs):
            try:
                # Dynamically load modules based on the function name
                # mod_path = f"oneflux_steps.ustar_cp_python.{name}"
                # mod = __import__(mod_path, fromlist=[name])
                # func = getattr(mod, name, None)
                # if nargout is present in kwargs then remove it
                if 'nargout' in kwargs:
                    kwargs.pop('nargout')
                func = globals().get(name)
                if callable(func):
                    return func(*args, **kwargs)
                else: 
                    warnings.warn(f"'function {name}' cannot be found", UserWarning)
            except ImportError:
                pass
            warnings.warn(f"'{name}' is not callable", UserWarning)
        return newfunc if globals().get(name) else None

# MATLAB Engine wrapper 
class MatlabEngine:
    def __init__(self, func):
        self.func = func
        self.out = io.StringIO()
        self.err = io.StringIO()
        name = func._name
        # make matlab stdout and stderr printed at the end of pytest
        atexit.register(lambda: (s := self.out.getvalue()) and print(f"{name} stdout:\n{s}"))
        atexit.register(lambda: (s := self.err.getvalue()) and print(f"{name} stderr:\n{s}"))

    def _repr_pretty_(self, *args):
        return "MATLAB"

    def __call__(self, *args, jsonencode=(), jsondecode=(), **kwargs):
        """
        Call the wrapped function with optional JSON encoding/decoding to handle the issue that non-scalar structs (arrays of structs) cannot be returned from MATLAB functions to Python.
        Args:
            *args: Positional arguments to pass to the wrapped function.
            jsonencode (tuple, optional): Indices of output arguments to JSON encode (into string) before the matlab function returns.
            jsondecode (tuple, optional): Indices of input arguments to JSON decode (from string) at the beginning of the matlab function.
            **kwargs: Keyword arguments to pass to the wrapped function.
        Returns:
            The result of the wrapped function, with specified outputs JSON decoded if necessary.
        """

        if self.func._name == '_repr_pretty_':
            # Overload attempts to pretty print matlab engines (e.g., by hypothesis)
            return 'MATLAB'

        # For `convert` and `equal` we need to handle these directly here since
        # we have overriden `call`.
        if (self.func._name == "convert") | (self.func._name == "unconvert") | (self.func._name == "equal"):

          # Locally scoped definitions
          def _convert(x, index=None):
                if index == 'to_matlab': # Add 1 for index conversion to MATLAB, types: int, ndarray, list
                    print(index)
                    print("Before conversion: ", x)
                    if isinstance(x, (int, float, np.ndarray)):
                        x = x+1
                    elif isinstance(x, list):
                        x = np.asarray(x)+1
                    print("After conversion: ", x)
                return to_matlab_type(x)

          def _unconvert(x):
              if isinstance(x, matlab.double):
                x = np.array(x)
              if len(x) == 1:
                  return np.array(x[0])
              else:
                  return x

          def _equal(x, y):
              return compare_matlab_arrays(x, y)

          # Choose which function to call
          if self.func._name == "convert":
            #   print(*args)
              return _convert(*args)
          elif self.func._name == "equal":
              return _equal(*args)
          elif self.func._name == "unconvert":
              return _unconvert(*args)

        else:
          # Calls mostly going through to the MATLAB engine
          args = list(args)
          if jsonencode:
              args.append(['jsonencode'] + [i+1 for i in jsonencode])
          if jsondecode:
              for i in jsondecode:
                  args[i] = json.dumps(args[i])
              args.append(['jsondecode'] + [i+1 for i in jsondecode])
          out = kwargs.pop('stdout', self.out)
          err = kwargs.pop('stderr', self.err)
          ret = self.func(*args, **kwargs, stdout=out, stderr=err)
          if jsonencode:
              nargout = kwargs.get('nargout', 1)
              if nargout <= 1:
                  ret = [ret]
              else:
                  ret = list(ret)
              for j in jsonencode:
                  ret[j] = json.loads(ret[j], object_hook=none2nan)
              if nargout <= 1:
                  ret = ret[0]

       # # Some alternate approach here
       # nargout = kwargs.get('nargout', 1)
        # if nargout <= 1:
        #     ret = [ret]
        # else:
        #     ret = list(ret)
        # for j, y in enumerate(ret):
        #     if j in jsonencode:
        #         y = json.loads(y, object_hook=lambda d:
        #             {k: np.nan if v is None else v for k, v in d.items()})
        #         ret[j] = struct(y)
        #     elif isinstance(y, np.ndarray):
        #         ret[j] = matlabarray(y)
        # if nargout <= 1:
        #     ret = ret[0]
        # return ret

          return ret

def mf_factory(cls, *args, **kwargs):
    f = object.__new__(MatlabFunc)
    f.__init__(*args, **kwargs)
    return MatlabEngine(f)
MatlabFunc.__new__ = mf_factory

@pytest.fixture(scope = "session")
def get_languages():

    return ["python", "matlab"]

@pytest.fixture(scope="session")
def test_engine(language, refactored=True):
    """
    Pytest fixture to start a 'running engine' which allows multiple languages
    to be targetted
    """
    # if request.param == "translated":  # return the translated python module
    #     import oneflux_steps.ustar_cp_python_auto as eng
    #     yield eng
    #     return
    if language == 'python':
        yield PythonEngine()  # Assuming a defined PythonEngine class elsewhere
    else:

        """
        Pytest fixture to start a MATLAB engine session, add a specified directory
        to the MATLAB path, and clean up after the tests.

        This fixture initializes the MATLAB engine, adds the directory containing
        MATLAB functions to the MATLAB path, and then yields the engine instance
        for use in tests. After the tests are done, the MATLAB engine is properly
        closed.

        Args:
          refactored (bool, optional): If True, use the refactored code path
              'oneflux_steps/ustar_cp_refactor_wip/'. Defaults to True, using
              the 'oneflux_steps/ustar_cp_refactor_wip/' path.

        Yields:
          matlab.engine.MatlabEngine: The MATLAB engine instance for running MATLAB
              functions within tests.

        After the tests complete, the MATLAB engine is closed automatically.
        """
        # Start MATLAB engine
        eng = matlab.engine.start_matlab()

        current_dir = os.getcwd()
        code_path = 'oneflux_steps/ustar_cp_refactor_wip/' if refactored else 'oneflux_steps/ustar_cp'

        # Add the directory containing your MATLAB functions to the MATLAB path
        matlab_function_path = os.path.join(current_dir, code_path)
        eng.addpath(matlab_function_path, nargout=0)

        def _add_all_subdirs_to_matlab_path(path, test_engine):
            # Recursively find all subdirectories
            for root, dirs, files in os.walk(path):
                # Add each directory to the MATLAB path
                test_engine.addpath(root, nargout=0)  # nargout=0 suppresses output

            return

        # Add the base directory and all its subdirectories to MATLAB path
        _add_all_subdirs_to_matlab_path(matlab_function_path, eng)

        yield eng

        #Close MATLAB engine after tests are done
        eng.quit()


@pytest.fixture
def setup_folders(tmp_path, request, testcase: str = "US_ARc"):
    """
    Fixture to set up input and output folders for tests by copying all files
    from a specified local directory.

    Args:
        tmp_path: A pytest fixture that provides a temporary directory unique to
                  the test invocation.
        testcase (str): The name of the subdirectory under 'tests/test_artifacts/'
                        that contains the test files.

    Returns:
        tuple: A tuple containing the paths to the temporary input, the reference output, and
               the empty output directories as strings.
    """

    # If 'testcase' is provided by the test function, use its value
    if 'testcase' in request.fixturenames:
        testcase = request.getfixturevalue('testcase')

    # Define paths for the temporary directories
    input_folder = tmp_path / "input"
    reference_output_folder = tmp_path / "ref_output"
    output_folder = tmp_path / "output"

    # Cleanup just in case
    for folder in [input_folder, reference_output_folder, output_folder]:
        if folder.exists():
            shutil.rmtree(folder)

    # Create the output directory (starts empty)
    output_folder.mkdir()

    # Pattern to match directories starting with the `testcase` name
    pattern = os.path.join('tests/test_artifacts', f'{testcase}*')

    # Use glob to find directories that match the pattern
    matching_dirs = glob.glob(pattern)

    # Assuming you want the first matching directory
    if matching_dirs:
        if len(matching_dirs) == 1:
            testcase_path = matching_dirs[0]
        else:
            raise ValueError(f"{pattern}: is not unique")
    else:
        raise FileNotFoundError(f"No matching directory found for pattern: {pattern}")

    data_path= os.path.join(testcase_path, '05_ustar_cp')

    # Copy all files and directories from the testcase input dir to the temporary input folder
    inputs = os.path.join(data_path, 'input')
    if os.path.exists(inputs):
        try:
            shutil.copytree(inputs, str(input_folder), dirs_exist_ok=True)
        except Exception as e:
            print(f"Error during copy: {e}")
    else:
        raise FileNotFoundError(f"Input directory {inputs} does not exist in testcase {testcase}")

    # Copy all files from the testcase ref_output dir to the temporary reference output folder
    ref_outputs = data_path
    if os.path.exists(ref_outputs):
        shutil.copytree(ref_outputs, str(reference_output_folder), dirs_exist_ok=True)
    else:
        raise FileNotFoundError(f"Reference output directory {ref_outputs} does not exist in testcase {testcase}")

    return str(input_folder), str(reference_output_folder), str(output_folder)

@pytest.fixture
def find_text_file():
    """
    Fixture to find the `report` file in the given folder, open it,
    extract its contents as a list of lines, and return the contents.

    Returns:
        function: A function that takes a folder path and returns the contents
                  of the first `.txt` file found in that folder as a list of lines.
    """
    def _find_text_file_in_folder(folder):
        # Search for a .txt file in the given folder
        for filename in os.listdir(folder):
            if filename.startswith('report'):
                # Construct the full file path
                file_path = os.path.join(folder, filename)

                # Open the file and read its contents as lines
                with open(file_path, 'r', encoding='utf-8') as file:
                    contents = file.readlines()  # Read the file as a list of lines
                return contents

        # If no .txt file is found, raise an error
        raise FileNotFoundError(f"No .txt file found in folder: {folder}")

    return _find_text_file_in_folder

@pytest.fixture
def extract_section_between_keywords():
    """
    Fixture to extract a section from a results txt file between two keywords.

    Args:
        data (list): The contents of the file as a list of lines.
        start_keyword (str): The keyword to start extracting from.
        end_keyword (str, optional): The keyword to stop extracting before.
                                     Defaults to None, which means take all text onward from the start keyword.

    Returns:
        function: A function that takes data (list of lines), start_keyword (str),
                  and end_keyword (str, optional), and returns the lines between the
                  start keyword and the end keyword, exclusive of the end keyword.
    """
    def _extract(data, start_keyword, end_keyword=None):
        # Find the index of the first occurrence of the start keyword
        start_idx = -1
        for i, line in enumerate(data):
            if line.strip().startswith(start_keyword):
                start_idx = i
                break  # Stop after finding the first occurrence

        if start_idx == -1:
            raise ValueError(f"No section starting with '{start_keyword}' found in the file")

        # If end_keyword is provided, find its index
        end_idx = len(data)  # Default to end of file if end_keyword is None
        if end_keyword:
            for i, line in enumerate(data[start_idx + 1:], start=start_idx + 1):
                if line.strip().startswith(end_keyword):
                    end_idx = i
                    break  # Stop after finding the first occurrence

        # Extract the section between the start and end keywords
        section = data[start_idx + 1:end_idx]  # Exclusive of both start and end keywords

        return section

    return _extract

def process_std_out(std_out):
    """
    Process standard output from a StringIO object into a list of lines.

    Args:
        std_out (StringIO): The StringIO object containing standard output.

    Returns:
        list: A list of lines from the standard output.
    """
    output = std_out.getvalue()
    output_lines = output.splitlines()
    return output_lines


def compare_text_blocks(text1, text2):
    """
    Compare two blocks of text after stripping whitespace.

    Args:
        text1 (str): The first block of text.
        text2 (str): The second block of text.

    Returns:
        bool: True if the stripped text blocks are identical, False otherwise.
    """
    return text1.replace('\n', '').strip() == text2.replace('\n', '').strip()

def to_matlab_type(data):
    """
    Converts various Python data types to their MATLAB equivalents.

    This function handles conversion of Python dictionaries, NumPy arrays, lists,
    and numeric types to MATLAB-compatible types using the `matlab` library.

    Args:
        data (any): The input data to be converted. Can be a dictionary, NumPy array,
                    list, integer, float, or other types.

    Returns:
        any: The converted data in a MATLAB-compatible format. The specific return type
             depends on the input data type:
             - dict: Converted to a MATLAB struct.
             - np.ndarray: Converted to MATLAB logical, double, or list.
             - list: Converted to MATLAB double array or cell array.
             - int, float: Converted to MATLAB double.
             - Other types: Returned as-is if already MATLAB-compatible.

    """
    if isinstance(data, dict):
        # Convert a Python dictionary to a MATLAB struct
        matlab_struct = matlab.struct()
        for key, value in data.items():
            matlab_struct[key] = to_matlab_type(value)  # Recursively handle nested structures
        return matlab_struct
    elif isinstance(data, np.ndarray):
        if data.dtype == bool:
            return matlab.logical(data.tolist())
        elif np.isreal(data).all():
            return matlab.double(data.tolist())
        else:
            return data.tolist()  # Convert non-numeric arrays to lists
    elif isinstance(data, list):
        # Convert Python list to MATLAB double array if all elements are numbers
        if all(isinstance(elem, (int, float)) for elem in flatten(data)):
            return matlab.double(data)
        else:
            # Create a cell array for lists containing non-numeric data
            return [to_matlab_type(elem) for elem in data]
    elif isinstance(data, (int, float)):
        return matlab.double([data])  # Convert single numbers
    else:
      return data  # If the data type is already MATLAB-compatible

def flatten(container):
    """
    Flatten a nested container into a single list.
    """
    for i in container:
        if isinstance(i, (list,tuple)):
            for j in flatten(i):
                yield j
        else:
            yield i

# Helper function to compare MATLAB double arrays element-wise, handling NaN comparisons
def compare_matlab_arrays(result, expected):
    if isinstance(result, float):
      # Floating point equality using numpy
      return np.isclose(result, expected, equal_nan=True)

    if not hasattr(result, '__len__') or not hasattr(expected, '__len__'):
        return np.allclose(result, expected, equal_nan=True)

    if isinstance(result, dict):
        if not isinstance(expected, dict):
            return False
        if set(result.keys()) != set(expected.keys()):
            return False
        return all(compare_matlab_arrays(result[k], expected[k]) for k in result.keys())

    if len(result) != len(expected):
        # Potentially we are in the situation where the MATLAB is wrapped in an extra layer of array
        if isinstance(result, matlab.double) and len(result) == 1:
            result = result[0]
            return all(compare_matlab_arrays(r, e) for r, e in zip(result, expected))
        else:
            return False

    if isinstance(result, matlab.double):
        return np.allclose(result, expected, equal_nan=True)

    # Recursive case
    return all(compare_matlab_arrays(r, e) for r, e in zip(result, expected))
    # ALT:
    #return all(objects_are_equal(r, e) for r, e in zip(result, expected))

def read_csv_with_csv_module(file_path):
    """
    Reads a CSV file and returns its contents as a NumPy array.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        numpy.ndarray: The contents of the CSV file as a NumPy array.
    """
    return np.loadtxt(file_path, delimiter=',')

def read_file(file_path):
    """
    Reads a file and returns its contents based on the file extension.

    Args:
        file_path (str): The path to the file to be read. The file can be either a CSV or a JSON file.

    Returns:
        dict or list: The contents of the file. Returns a list of dictionaries if the file is a CSV,
                      or a dictionary if the file is a JSON.

    Raises:
        ValueError: If the file extension is not supported.
    """
    # Check the file extension to differentiate between CSV and JSON
    if file_path.endswith('.csv'):
        return read_csv_with_csv_module(file_path)
    elif file_path.endswith('.json'):
        with open(file_path, 'r') as f:
            return none2nan(json.load(f))  # Load JSON file
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

def none2nan(obj):
    if isinstance(obj, dict):
        return {k: none2nan(v) for k, v in obj.items()}
    elif hasattr(obj, 'size'):
        return np.where(obj is None, np.nan, obj).tolist()
    elif isinstance(obj, list):
        return [none2nan(v) for v in obj]
    elif obj is None:
        return np.nan
    else:
        return obj

def parse_testcase(test_case: dict, path_to_artifacts: str):
    """
    Parses the test case data by reading file-based inputs and outputs if necessary.

    Args:
        test_case (dict): A dictionary containing a single test case's input and expected_output.
        path_to_artifacts (str): The path to the directory where test case artifacts are stored.

    Returns:
        tuple: A tuple containing two dictionaries:
            - inputs (dict): A dictionary with processed input data.
            - outputs (dict): A dictionary with processed expected output data.
    """
    inputs: dict = {}
    outputs: dict = {}

    for io_type in ['input', 'expected_output']:
        for key, value in test_case[io_type].items():  # Use test_case here
            if isinstance(value, str):  # Check if the value is a string (likely a file path)
                path = os.path.join(path_to_artifacts, test_case["id"], value)  # Use test_case here
                if os.path.exists(path):  # Check if the file exists
                    # Read the file using the fixture function and store the data
                    file_data = read_file(path)
                    if io_type == 'input':
                        inputs[key] = file_data
                    else:
                        outputs[key] = file_data
                else:
                    if io_type == 'input':
                        inputs[key] = value
                    else:
                        outputs[key] = value
            else:
                # If it's not a string, directly store the value in the inputs or outputs dictionary
                if io_type == 'input':
                    inputs[key] = value
                else:
                    outputs[key] = value

    return inputs, outputs