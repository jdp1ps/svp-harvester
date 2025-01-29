import pytest

from tests.fixtures.common import _json_data_from_file


@pytest.fixture(name="hal_api_doc_for_hash_1")
def fixture_hal_api_doc_for_hash_1(_base_path) -> dict:
    """
    Generate a HAL API response for a researcher in JSON format
    :param _base_path: test data directory base
    :return: HAL API response for one researcher in JSON format
    """
    return _hal_api_json_data_from_file(_base_path, "doc_for_hash_1")


@pytest.fixture(name="hal_api_doc_for_hash_2")
def fixture_hal_api_doc_for_hash_2(_base_path) -> dict:
    """
    Generate a HAL API response for a researcher in JSON format
    :param _base_path: test data directory base
    :return: HAL API response for one researcher in JSON format
    """
    return _hal_api_json_data_from_file(_base_path, "doc_for_hash_2")


@pytest.fixture(name="hal_api_docs_for_researcher")
def fixture_hal_api_docs_for_researcher(_base_path) -> dict:
    """
    Generate a HAL API response for a researcher in JSON format
    :param _base_path: test data directory base
    :return: HAL API response for one researcher in JSON format
    """
    return _hal_api_json_data_from_file(_base_path, "docs_for_researcher")


@pytest.fixture(name="hal_api_docs_with_inconsistent_structured_names")
def fixture_hal_api_docs_with_inconsistent_structured_names(_base_path) -> dict:
    """
    Generate a HAL API response for a researcher in JSON format
    with a number of first names / last names that do not match
    the number of contributors
    :param _base_path: test data directory base
    :return: HAL API response for one researcher in JSON format
    """
    return _hal_api_json_data_from_file(
        _base_path, "docs_with_inconsistent_structured_names"
    )


@pytest.fixture(name="hal_api_docs_with_contributor_identifiers")
def fixture_hal_api_docs_with_contributor_identifiers(_base_path) -> dict:
    """
    Generate a HAL API response for a researcher in JSON format
    :param _base_path: test data directory base
    :return: HAL API response for one researcher in JSON format
    """
    return _hal_api_json_data_from_file(_base_path, "docs_with_contributor_identifiers")


@pytest.fixture(name="hal_api_docs_for_researcher_with_uris")
def fixture_hal_api_docs_for_researcher_with_uris(_base_path) -> dict:
    """
    Generate a HAL API response for a researcher in JSON format
    :param _base_path: test data directory base
    :return: HAL API response for one researcher in JSON format
    """
    return _hal_api_json_data_from_file(_base_path, "docs_for_researcher_with_uris")


@pytest.fixture(name="hal_api_docs_for_researcher_version_1")
def fixture_hal_api_docs_for_researcher_version_1(_base_path) -> dict:
    """
    Generate the first version of the HAL API response for a researcher in JSON format
    :param _base_path: test data directory base
    :return: HAL API response for one researcher in JSON format
    """
    return _hal_api_json_data_from_file(_base_path, "docs_for_researcher_version_1")


@pytest.fixture(name="hal_api_docs_with_contributors_version_1")
def fixture_hal_api_docs_with_contributors_version_1(_base_path) -> dict:
    """
    Generate the first version of the HAL API response
    with contributors for a researcher in JSON format
    :param _base_path: test data directory base
    :return: HAL API response for one researcher in JSON format
    """
    return _hal_api_json_data_from_file(_base_path, "docs_with_contributors_version_1")


@pytest.fixture(name="hal_api_docs_with_inconsistent_contributors")
def fixture_hal_api_docs_with_inconsistent_contributors(_base_path) -> dict:
    """
    Generate a json response with contributors
    having the same identifier but different names
    :param _base_path: test data directory base
    :return: HAL API response for inconsistent contributors in JSON format
    """
    return _hal_api_json_data_from_file(
        _base_path, "docs_with_inconsistent_contributors"
    )


@pytest.fixture(name="hal_api_docs_for_researcher_version_2")
def fixture_hal_api_docs_for_researcher_version_2(_base_path) -> dict:
    """
    Generate the second version of the HAL API response for a researcher in JSON format
    with a publication unchanged, a publication updated, a publication created a publication deleted
    :param _base_path: test data directory base
    :return: HAL API response for one researcher in JSON format
    """
    return _hal_api_json_data_from_file(_base_path, "docs_for_researcher_version_2")


@pytest.fixture(name="hal_api_docs_with_contributors_version_2")
def fixture_hal_api_docs_with_contributors_version_2(_base_path) -> dict:
    """
    Generate the second version of the HAL API response
    with contributors for a researcher in JSON format
    :param _base_path: test data directory base
    :return: HAL API response for one researcher in JSON format
    """
    return _hal_api_json_data_from_file(_base_path, "docs_with_contributors_version_2")


@pytest.fixture(name="hal_api_docs_with_same_kw_twice")
def fixture_hal_api_docs_with_same_kw_twice(_base_path) -> dict:
    """
    Generate a HAL API response for one researcher in JSON format
    :param _base_path: test data directory base
    :return: HAL API response for one researcher in JSON format
    """
    return _hal_api_json_data_from_file(_base_path, "docs_with_same_kw_twice")


@pytest.fixture(name="hal_api_docs_with_date_inconsistency")
def fixture_hal_api_docs_with_date_inconsistency(_base_path) -> dict:
    """
    Generate a HAL API response for one researcher in JSON format
    :param _base_path: test data directory base
    :return: HAL API response for one researcher in JSON format
    """
    return _hal_api_json_data_from_file(_base_path, "docs_with_date_inconsistency")


@pytest.fixture(name="hal_api_docs_with_date_invalid_format")
def fixture_hal_api_docs_with_date_invalid_format(_base_path) -> dict:
    """
    Generate a HAL API response for one researcher in JSON format
    :param _base_path: test data directory base
    :return: HAL API response for one researcher in JSON format
    """
    return _hal_api_json_data_from_file(_base_path, "docs_with_date_invalid_format")


def _hal_api_json_data_from_file(base_path, file_name) -> dict:
    file_path = f"data/hal_api/{file_name}.json"
    return _json_data_from_file(base_path, file_path)
