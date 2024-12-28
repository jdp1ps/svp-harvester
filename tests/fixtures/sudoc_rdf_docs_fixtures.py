import pathlib

import pytest
from rdflib import Graph, URIRef

from app.harvesters.idref.idref_harvester import IdrefHarvester
from app.harvesters.rdf_harvester_raw_result import RdfHarvesterRawResult as RdfResult


@pytest.fixture(name="sudoc_rdf_result_for_book")
def fixture_sudoc_rdf_result_for_book(sudoc_rdf_graph_for_book) -> RdfResult:
    """Rdf result from sudoc wrapped in a RdfHarvesterRawResult"""
    return RdfResult(
        payload=sudoc_rdf_graph_for_book,
        source_identifier=URIRef("http://www.sudoc.fr/260799939/id"),
        formatter_name=IdrefHarvester.Formatters.SUDOC_RDF.value,
    )


@pytest.fixture(name="sudoc_rdf_result_for_doc")
def fixture_sudoc_rdf_result_for_doc(sudoc_rdf_graph_for_doc) -> RdfResult:
    """Rdf result from sudoc wrapped in a RdfHarvesterRawResult"""
    return RdfResult(
        payload=sudoc_rdf_graph_for_doc,
        source_identifier=URIRef("http://www.sudoc.fr/193726130/id"),
        formatter_name=IdrefHarvester.Formatters.SUDOC_RDF.value,
    )


@pytest.fixture(name="sudoc_rdf_result_for_thesis")
def fixture_sudoc_rdf_result_for_thesis(sudoc_rdf_graph_for_thesis) -> RdfResult:
    """Rdf result from sudoc wrapped in a RdfHarvesterRawResult"""
    return RdfResult(
        payload=sudoc_rdf_graph_for_thesis,
        source_identifier=URIRef("http://www.sudoc.fr/253147565/id"),
        formatter_name=IdrefHarvester.Formatters.SUDOC_RDF.value,
    )


@pytest.fixture(name="sudoc_rdf_result_for_thesis_with_nnt_in_manifestation_uri")
def fixture_sudoc_rdf_result_for_thesis_with_nnt_in_manifestation_uri(
    sudoc_rdf_graph_for_thesis_with_nnt_in_manifestation_uri,
) -> RdfResult:
    """
    Rdf result from sudoc wrapped in a RdfHarvesterRawResult
    with NNT only in the manifestation URI
    and not in bibo:uri
    """
    return RdfResult(
        payload=sudoc_rdf_graph_for_thesis_with_nnt_in_manifestation_uri,
        source_identifier=URIRef("http://www.sudoc.fr/253147565/id"),
        formatter_name=IdrefHarvester.Formatters.SUDOC_RDF.value,
    )


@pytest.fixture(name="sudoc_rdf_result_for_doc_with_invalid_created")
def fixture_sudoc_rdf_result_for_doc_with_invalid_created(
    sudoc_rdf_graph_for_doc_with_invalid_created,
) -> RdfResult:
    """Rdf result from sudoc wrapped in a RdfHarvesterRawResult"""
    return RdfResult(
        payload=sudoc_rdf_graph_for_doc_with_invalid_created,
        source_identifier=URIRef("http://www.sudoc.fr/193726130/id"),
        formatter_name=IdrefHarvester.Formatters.SUDOC_RDF.value,
    )


@pytest.fixture(name="sudoc_rdf_result_for_doc_without_title")
def fixture_sudoc_rdf_result_for_doc_without_title(
    sudoc_rdf_graph_for_doc_without_title,
) -> RdfResult:
    """Rdf result from sudoc wrapped in a RdfHarvesterRawResult"""
    return RdfResult(
        payload=sudoc_rdf_graph_for_doc_without_title,
        source_identifier=URIRef("http://www.sudoc.fr/193726130/id"),
        formatter_name=IdrefHarvester.Formatters.SUDOC_RDF.value,
    )


@pytest.fixture(name="sudoc_rdf_graph_for_book")
def fixture_sudoc_rdf_graph_for_book(_base_path) -> Graph:
    """Rdf graph from sudoc rdf file"""
    return _sudoc_rdf_graph_from_file(_base_path, "document_book")


@pytest.fixture(name="sudoc_rdf_graph_for_doc_without_title")
def fixture_sudoc_rdf_graph_for_doc_without_title(_base_path) -> Graph:
    """Rdf graph from sudoc rdf file"""
    return _sudoc_rdf_graph_from_file(_base_path, "document_without_title")


@pytest.fixture(name="sudoc_rdf_graph_for_doc")
def fixture_sudoc_rdf_graph_for_doc(_base_path) -> Graph:
    """Rdf graph from sudoc rdf file"""
    return _sudoc_rdf_graph_from_file(_base_path, "document")


@pytest.fixture(name="sudoc_rdf_graph_for_doc_with_invalid_created")
def fixture_sudoc_rdf_graph_for_doc_with_invalid_created(_base_path) -> Graph:
    """Rdf graph from sudoc rdf file"""
    return _sudoc_rdf_graph_from_file(_base_path, "document_with_invalid_created")


@pytest.fixture(name="sudoc_rdf_result_for_journal")
def fixture_sudoc_rdf_result_for_journal(_base_path) -> Graph:
    """Rdf graph from sudoc journal rdf file"""
    return _sudoc_rdf_graph_from_file(_base_path, "journal")


@pytest.fixture(name="sudoc_rdf_graph_for_hash_1")
def fixture_sudoc_rdf_graph_for_hash_1(_base_path) -> Graph:
    """Rdf graph from sudoc rdf file"""
    return _sudoc_rdf_graph_from_file(_base_path, "document_for_hash_1")


@pytest.fixture(name="sudoc_rdf_graph_for_hash_2")
def fixture_sudoc_rdf_graph_for_hash_2(_base_path) -> Graph:
    """Rdf graph from sudoc rdf file"""
    return _sudoc_rdf_graph_from_file(_base_path, "document_for_hash_2")


@pytest.fixture(name="sudoc_rdf_graph_for_thesis")
def fixture_sudoc_rdf_graph_for_thesis(_base_path) -> Graph:
    """Rdf graph from sudoc rdf file"""
    return _sudoc_rdf_graph_from_file(_base_path, "thesis")


@pytest.fixture(name="sudoc_rdf_graph_for_thesis_with_nnt_in_manifestation_uri")
def fixture_sudoc_rdf_graph_for_thesis_with_nnt_in_manifestation_uri(
    _base_path,
) -> Graph:
    """Rdf graph from sudoc rdf file"""
    return _sudoc_rdf_graph_from_file(
        _base_path, "thesis_with_nnt_in_manifestation_uri"
    )


@pytest.fixture(name="sudoc_rdf_xml_with_empty_date_fields")
def fixture_sudoc_rdf_xml_with_empty_date_fields(_base_path) -> str:
    """Rdf xml from sudoc rdf file"""
    file_path = "data/sudoc_rdf/document_with_empty_date_fields.rdf"
    return _rdf_xml_file_content(_base_path, file_path)


@pytest.fixture(name="sudoc_rdf_xml_for_doc")
def fixture_sudoc_rdf_xml_for_doc(_base_path) -> str:
    """Rdf xml from sudoc rdf file"""
    return _rdf_xml_file_content(_base_path, "document")


def _sudoc_rdf_graph_from_file(base_path, file_name) -> Graph:
    file_path = f"data/sudoc_rdf/{file_name}.rdf"
    return _rdf_graph_from_xml_file(base_path, file_path)


def _rdf_graph_from_xml_file(base_path, file_path) -> Graph:
    input_data = _rdf_xml_file_content(base_path, file_path)
    return Graph().parse(data=input_data, format="xml")


def _rdf_xml_file_content(base_path, file_path):
    file = pathlib.Path(base_path / file_path)
    with open(file, encoding="utf-8") as xml_file:
        return xml_file.read()
