import pytest

from app.harvesters.sparql_harvester_raw_result import SparqlHarvesterRawResult
from tests.fixtures.common import _json_data_from_file


@pytest.fixture(name="idref_sparql_result_for_doc")
def fixture_idref_sparql_result_for_doc(
    idref_pub_converted_1,
) -> SparqlHarvesterRawResult:
    """Sparql result from idref wrapped in a SparqlHarvesterRawResult"""
    return SparqlHarvesterRawResult(
        source_identifier=idref_pub_converted_1["uri"],
        payload=idref_pub_converted_1,
        formatter_name="Idref",
    )


@pytest.fixture(name="idref_pub_converted_1")
def fixture_idref_pub_converted_1(_base_path) -> dict:
    """
    Generate a Idref publication converted from a Idref Sparql endpoint response

    :return: Idref publication converted from a Idref Sparql endpoint response
    """
    return _idref_sparql_endpoint_json_results_from_file(
        _base_path, "idref_result_with_idref_doc_1"
    )


@pytest.fixture(name="idref_pub_converted_2")
def fixture_idref_pub_converted_2(_base_path) -> dict:
    """
    Generate a Idref publication converted from a Idref Sparql endpoint response

    :return: Idref publication converted from a Idref Sparql endpoint response
    """
    return _idref_sparql_endpoint_json_results_from_file(
        _base_path, "idref_result_with_idref_doc_2"
    )


@pytest.fixture(name="idref_sparql_endpoint_results_with_idref_pubs")
def fixture_idref_sparql_endpoint_results_with_idref_pubs(_base_path) -> dict:
    """
    Generate an Idref Sparql endpoint response with Idref publications in JSON format

    :param _base_path: test data directory base
    :return: Idref Sparql endpoint response for one researcher in JSON format
    """
    return _idref_sparql_endpoint_json_results_from_file(
        _base_path, "idref_result_with_idref_references"
    )


@pytest.fixture(name="idref_sparql_endpoint_results_with_test_concept")
def fixture_idref_sparql_endpoint_results_with_test_concept(_base_path) -> dict:
    """
    Generate an Idref Sparql endpoint response with an Idref publications in JSON format
    containing a test concept allowed for Idref concept solver tests

    :param _base_path: test data directory base
    :return: Idref Sparql endpoint response for one researcher in JSON format
    """
    return _idref_sparql_endpoint_json_results_from_file(
        _base_path, "idref_result_with_test_concept"
    )


@pytest.fixture(name="idref_sparql_endpoint_results_with_sudoc_pub")
def fixture_idref_sparql_endpoint_results_with_sudoc_pub(_base_path) -> dict:
    """
    Generate an Idref Sparql endpoint response with Sudoc publication in JSON format

    :param _base_path: test data directory base
    :return: Idref Sparql endpoint response for one researcher in JSON format
    """
    return _idref_sparql_endpoint_json_results_from_file(
        _base_path, "idref_result_with_sudoc_reference"
    )


@pytest.fixture(name="idref_sparql_endpoint_results_with_sudoc_cached_pub")
def fixture_idref_sparql_endpoint_results_with_sudoc_cached_pub(_base_path) -> dict:
    """
    Generate an Idref Sparql endpoint response with Sudoc publication in JSON format
    whose uri is already in the redis cache
    Speacial id used : 070266875

    :param _base_path: test data directory base
    :return: Idref Sparql endpoint response for one researcher in JSON format
    """
    return _idref_sparql_endpoint_json_results_from_file(
        _base_path, "idref_result_with_sudoc_cached_reference"
    )


@pytest.fixture(name="idref_sparql_endpoint_response_for_concept")
def fixture_idref_sparql_endpoint_response_for_concept(_base_path) -> dict:
    """
    Generate an Idref Sparql endpoint concept response

    :param _base_path: test data directory base
    :return: Idref Sparql endpoint response
    """
    return _idref_sparql_endpoint_json_results_from_file(
        _base_path, "idref_sparql_endpoint_response_for_concept"
    )


@pytest.fixture(name="idref_sparql_endpoint_response_for_concept_multilang")
def fixture_idref_sparql_endpoint_response_for_concept_multilang(_base_path) -> dict:
    """
    Generate an Idref Sparql endpoint concept response

    :param _base_path: test data directory base
    :return: Idref Sparql endpoint response
    """
    return _idref_sparql_endpoint_json_results_from_file(
        _base_path, "idref_sparql_endpoint_response_for_concept_multilang"
    )


@pytest.fixture(name="idref_sparql_endpoint_response_for_concept_non_preferred_languages")
def fixture_idref_sparql_endpoint_response_for_concept_concept_non_preferred_languages(
        _base_path
) -> dict:
    """
    Generate an Idref Sparql endpoint concept response

    :param _base_path: test data directory base
    :return: Idref Sparql endpoint response
    """
    return _idref_sparql_endpoint_json_results_from_file(
        _base_path, "idref_sparql_endpoint_response_for_concept_non_preferred_languages"
    )


def _idref_sparql_endpoint_json_results_from_file(base_path, file_name) -> dict:
    file_path = f"data/idref_sparql_endpoint/{file_name}.json"
    return _json_data_from_file(base_path, file_path)
