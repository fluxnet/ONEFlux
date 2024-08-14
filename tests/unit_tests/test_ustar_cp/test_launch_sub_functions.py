"""test refactored launch.m subfunctions"""

# test_functions.py

import pytest

def test_validate_and_prepare_path_empty_input(matlab_engine):
    # Test validateAndPreparePath with an empty input
    result = matlab_engine.validateAndPreparePath('', 'C:\\', nargout=1)
    assert result == 'C:\\\\'

def test_validate_and_prepare_path_relative_input(matlab_engine):
    # Test validateAndPreparePath with a relative input
    result = matlab_engine.validateAndPreparePath('relative_path', 'C:\\', nargout=1)
    assert result == 'C:\\\\relative_path\\\\'

def test_validate_and_prepare_path_absolute_input(matlab_engine):
    # Test validateAndPreparePath with an absolute input
    result = matlab_engine.validateAndPreparePath('C:\\absolute_path', '', nargout=1)
    assert result == 'C:\\absolute_path\\'

def test_load_dataset_valid_file(matlab_engine, tmp_path):
    # Create a temporary file to test loadDataset
    test_file = tmp_path / "test_file.csv"
    test_file.write_text("site,example\nyear,2022\n")

    dataset, success = matlab_engine.loadDataset(str(test_file), nargout=2)
    assert success is True
    assert dataset[0] == 'site,example'

def test_load_dataset_invalid_file(matlab_engine):
    # Test loadDataset with a non-existent file
    dataset, success = matlab_engine.loadDataset('non_existent_file.csv', nargout=2)
    assert success is False
    assert dataset == []

def test_parse_metadata_valid(matlab_engine):
    # Test parseMetadata with a valid dataset
    dataset = ['site,example', 'year,2022', '', '', '', '', '', '', '', 'notes,some note']
    site, year, notes, success = matlab_engine.parseMetadata(dataset, nargout=4)
    assert success is True
    assert site == 'example'
    assert year == '2022'
    assert 'some note' in notes[0]

def test_parse_metadata_invalid(matlab_engine):
    # Test parseMetadata with an invalid dataset
    dataset = ['invalid_data']
    site, year, notes, success = matlab_engine.parseMetadata(dataset, nargout=4)
    assert success is False
    assert site == ''
    assert year == ''
    assert notes == []

def test_import_data_valid(matlab_engine, tmp_path):
    # Create a temporary file to test importData
    test_file = tmp_path / "test_file.csv"
    test_file.write_text("site,example\nyear,2022\nheader1,header2,header3\n1,2,3\n4,5,6\n")

    header, data, success = matlab_engine.importData(str(test_file), 1, nargout=3)
    assert success is True
    assert len(header) > 0
    assert len(data) > 0

def test_import_data_invalid(matlab_engine):
    # Test importData with a non-existent file
    header, data, success = matlab_engine.importData('non_existent_file.csv', 1, nargout=3)
    assert success is False
    assert header == []
    assert data == []

def test_match_columns_valid(matlab_engine):
    # Test matchColumns with a valid header
    header = ['USTAR', 'NEE', 'TA', 'PPFD_IN', 'SW_IN']
    input_columns_names = ['USTAR', 'NEE', 'TA', 'PPFD_IN', 'SW_IN']
    columns_index, ppfd_from_rg, success = matlab_engine.matchColumns(header, input_columns_names, 4, nargout=3)
    assert success is True
    assert columns_index[0] == 1

def test_match_columns_invalid(matlab_engine):
    # Test matchColumns with an invalid header
    header = ['Invalid1', 'Invalid2']
    input_columns_names = ['USTAR', 'NEE', 'TA', 'PPFD_IN', 'SW_IN']
    columns_index, ppfd_from_rg, success = matlab_engine.matchColumns(header, input_columns_names, 4, nargout=3)
    assert success is False

def test_extract_and_prepare_data_valid(matlab_engine):
    # Test extractAndPrepareData with valid data
    data = [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]]
    columns_index = [1, 2, 3, 4, 5]
    ppfd_from_rg = 0
    uStar, NEE, Ta, PPFD, Rg = matlab_engine.extractAndPrepareData(data, columns_index, 1, 2, 3, 4, 5, ppfd_from_rg, nargout=5)
    assert len(uStar) > 0
    assert len(NEE) > 0
    assert len(Ta) > 0
    assert len(PPFD) > 0
    assert len(Rg) > 0

def test_extract_and_prepare_data_invalid(matlab_engine):
    # Test extractAndPrepareData with invalid data
    data = [[-9999, -9999, -9999, -9999, -9999]]
    columns_index = [1, 2, 3, 4, 5]
    ppfd_from_rg = 0
    uStar, NEE, Ta, PPFD, Rg = matlab_engine.extractAndPrepareData(data, columns_index, 1, 2, 3, 4, 5, ppfd_from_rg, nargout=5)
    assert all([v == float('nan') for v in uStar])
    assert all([v == float('nan') for v in NEE])
    assert all([v == float('nan') for v in Ta])
    assert all([v == float('nan') for v in PPFD])
    assert all([v == float('nan') for v in Rg])

def test_validate_data_valid(matlab_engine):
    # Test validateData with valid data
    valid = matlab_engine.validateData([1, 2], [1, 2], [1, 2], [1, 2], nargout=1)
    assert valid is True

def test_validate_data_invalid(matlab_engine):
    # Test validateData with invalid data
    valid = matlab_engine.validateData([float('nan'), float('nan')], [float('nan'), float('nan')], [], [], nargout=1)
    assert valid is False

def test_generate_time_series(matlab_engine):
    # Test generateTimeSeries with valid uStar data
    t = matlab_engine.generateTimeSeries([1, 2, 3], nargout=1)
    assert len(t) == 3

def test_process_seasonal_analysis_valid(matlab_engine, tmp_path):
    # Test processSeasonalAnalysis with valid inputs
    t = [1, 2, 3]
    NEE = [1, 2, 3]
    uStar = [1, 2, 3]
    T = [1, 2, 3]
    fNight = [0, 1, 0]
    site = 'example_site'
    year = '2022'
    notes = ['note1', 'note2']
    output_folder = tmp_path

    Cp, success = matlab_engine.processSeasonalAnalysis(t, NEE, uStar, T, fNight, site, year, str(output_folder), notes, nargout=2)
    assert success is True
    assert len(Cp) > 0

def test_process_seasonal_analysis_invalid(matlab_engine, tmp_path):
    # Test processSeasonalAnalysis with invalid inputs
    t = []
    NEE = []
    uStar = []
    T = []
    fNight = []
    site = 'example_site'
    year = '2022'
    notes = ['note1', 'note2']
    output_folder = tmp_path

    Cp, success = matlab_engine.processSeasonalAnalysis(t, NEE, uStar, T, fNight, site, year, str(output_folder), notes, nargout=2)
    assert success is False
    assert len(Cp) == 0
