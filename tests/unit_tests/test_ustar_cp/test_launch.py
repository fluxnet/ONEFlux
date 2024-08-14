"""Module for testing launch.m"""

import matlab.engine
import pytest
import os
import shutil

# Helper functions to create test data
def create_invalid_csv_file(file_path, lines):
    with open(file_path, 'w') as f:
        f.writelines("\n".join(lines))

def create_valid_csv_file(file_path):
    with open(file_path, 'w') as f:
        f.writelines([
            "site, mysite\n",
            "year, 2023\n",
            "lat, 45.0\n",
            "lon, -93.0\n",
            "timezone, 6\n",
            "htower, 30\n",
            "timeres, 0.1\n",
            "Sc_negl, some\n",
            "notes, some notes\n",
            "USTAR,NEE,TA,PPFD_IN,SW_IN\n",
            "0.3,-0.5,15.0,200,800\n"
        ])

def create_csv_file_missing_columns(file_path):
    with open(file_path, 'w') as f:
        f.writelines([
            "site, mysite\n",
            "year, 2023\n",
            "lat, 45.0\n",
            "lon, -93.0\n",
            "timezone, 6\n",
            "htower, 30\n",
            "timeres, 0.1\n",
            "Sc_negl, some\n",
            "notes, some notes\n",
            "USTAR,TA,PPFD_IN,SW_IN\n",
            "0.3,15.0,200,800\n"
        ])

def create_csv_file_with_empty_nee(file_path):
    with open(file_path, 'w') as f:
        f.writelines([
            "site, mysite\n",
            "year, 2023\n",
            "lat, 45.0\n",
            "lon, -93.0\n",
            "timezone, 6\n",
            "htower, 30\n",
            "timeres, 0.1\n",
            "Sc_negl, some\n",
            "notes, some notes\n",
            "USTAR,NEE,TA,PPFD_IN,SW_IN\n",
            "0.3,NaN,15.0,200,800\n"
        ])

def create_csv_file_with_empty_ustar(file_path):
    with open(file_path, 'w') as f:
        f.writelines([
            "site, mysite\n",
            "year, 2023\n",
            "lat, 45.0\n",
            "lon, -93.0\n",
            "timezone, 6\n",
            "htower, 30\n",
            "timeres, 0.1\n",
            "Sc_negl, some\n",
            "notes, some notes\n",
            "USTAR,NEE,TA,PPFD_IN,SW_IN\n",
            "NaN,-0.5,15.0,200,800\n"
        ])

# Test class using pytest
@pytest.fixture(scope="module")
def matlab_engine():
    eng = matlab.engine.start_matlab()
    yield eng
    eng.quit()

@pytest.fixture
def setup_folders():
    input_folder = os.path.join(os.getcwd(), 'input_folder')
    output_folder = os.path.join(os.getcwd(), 'output_folder')
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)
    yield input_folder, output_folder
    shutil.rmtree(input_folder, ignore_errors=True)
    shutil.rmtree(output_folder, ignore_errors=True)

def test_missing_input_folder(matlab_engine, setup_folders):
    _, output_folder = setup_folders
    exitcode = matlab_engine.launch('', output_folder)
    assert exitcode == 0

def test_missing_output_folder(matlab_engine, setup_folders):
    input_folder, _ = setup_folders
    exitcode = matlab_engine.launch(input_folder, '')
    assert exitcode == 0

def test_invalid_input_folder(matlab_engine, setup_folders):
    _, output_folder = setup_folders
    exitcode = matlab_engine.launch('non_existent_folder', output_folder)
    assert exitcode == 1

def test_file_without_site_keyword(matlab_engine, setup_folders):
    input_folder, output_folder = setup_folders
    create_invalid_csv_file(os.path.join(input_folder, 'invalid_file.csv'), ['not_site, 2023, 45.0, -93.0, 6, 30, 0.1, some notes'])
    exitcode = matlab_engine.launch(input_folder, output_folder)
    assert exitcode == 1

def test_file_without_year_keyword(matlab_engine, setup_folders):
    input_folder, output_folder = setup_folders
    create_invalid_csv_file(os.path.join(input_folder, 'invalid_file.csv'), ['site, mysite, 45.0, -93.0, 6, 30, 0.1, some notes'])
    exitcode = matlab_engine.launch(input_folder, output_folder)
    assert exitcode == 1

def test_file_without_lat_keyword(matlab_engine, setup_folders):
    input_folder, output_folder = setup_folders
    create_invalid_csv_file(os.path.join(input_folder, 'invalid_file.csv'), ['site, mysite, year, 2023, -93.0, 6, 30, 0.1, some notes'])
    exitcode = matlab_engine.launch(input_folder, output_folder)
    assert exitcode == 1

def test_file_with_all_required_keywords(matlab_engine, setup_folders):
    input_folder, output_folder = setup_folders
    create_valid_csv_file(os.path.join(input_folder, 'valid_file.csv'))
    exitcode = matlab_engine.launch(input_folder, output_folder)
    assert exitcode == 0

def test_file_missing_columns(matlab_engine, setup_folders):
    input_folder, output_folder = setup_folders
    create_csv_file_missing_columns(os.path.join(input_folder, 'missing_columns_file.csv'))
    exitcode = matlab_engine.launch(input_folder, output_folder)
    assert exitcode == 1

def test_file_with_empty_nee(matlab_engine, setup_folders):
    input_folder, output_folder = setup_folders
    create_csv_file_with_empty_nee(os.path.join(input_folder, 'empty_nee_file.csv'))
    exitcode = matlab_engine.launch(input_folder, output_folder)
    assert exitcode == 0

def test_file_with_empty_ustar(matlab_engine, setup_folders):
    input_folder, output_folder = setup_folders
    create_csv_file_with_empty_ustar(os.path.join(input_folder, 'empty_ustar_file.csv'))
    exitcode = matlab_engine.launch(input_folder, output_folder)
    assert exitcode == 0

def test_valid_file_processing(matlab_engine, setup_folders):
    input_folder, output_folder = setup_folders
    create_valid_csv_file(os.path.join(input_folder, 'valid_file.csv'))
    exitcode = matlab_engine.launch(input_folder, output_folder)
    assert exitcode == 0

    # Verify the output file is created
    output_files = os.listdir(output_folder)
    assert len(output_files) == 1


