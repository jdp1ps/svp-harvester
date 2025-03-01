import pathlib
import pytest
from rdflib import Graph
from app.harvesters.idref.idref_harvester import IdrefHarvester

from app.harvesters.rdf_harvester_raw_result import RdfHarvesterRawResult


@pytest.fixture(name="persee_rdf_result_for_doc")
def fixture_persee_rdf_result_for_doc(
    persee_rdf_graph_for_doc,
) -> RdfHarvesterRawResult:
    """Rdf result from persee wrapped in a RdfHarvesterRawResult"""
    return RdfHarvesterRawResult(
        payload=persee_rdf_graph_for_doc,
        source_identifier="http://data.persee.fr/doc/hista_0992-2059_1998_num_42_1_2826#Web",
        formatter_name=IdrefHarvester.Formatters.PERSEE_RDF.value,
    )


@pytest.fixture(name="persee_rdf_graph_for_doc")
def fixture_persee_rdf_graph_for_doc(_base_path) -> Graph:
    """Rdf graph from persee rdf file"""
    return _persee_rdf_graph_from_file(_base_path, "persee_document")


@pytest.fixture(name="persee_rdf_result_for_doc_with_invalid_dateofpublication")
def fixture_persee_rdf_result_for_doc_with_invalid_dateofpublication(
    persee_rdf_graph_for_doc_with_invalid_dateofpublication,
) -> RdfHarvesterRawResult:
    """Rdf result from persee wrapped in a RdfHarvesterRawResult"""
    return RdfHarvesterRawResult(
        payload=persee_rdf_graph_for_doc_with_invalid_dateofpublication,
        source_identifier="http://data.persee.fr/doc/hista_0992-2059_1998_num_42_1_2826#Web",
        formatter_name=IdrefHarvester.Formatters.PERSEE_RDF.value,
    )


@pytest.fixture(name="persee_rdf_graph_for_doc_with_invalid_dateofpublication")
def fixture_persee_rdf_graph_for_doc_with_invalid_dateofpublication(
    _base_path,
) -> Graph:
    """Rdf graph from persee rdf file"""
    return _persee_rdf_graph_from_file(
        _base_path, "persee_document_with_invalid_dateofpublication"
    )


@pytest.fixture(name="persee_rdf_result_for_doc_with_invalid_dateofprintpublication")
def fixture_persee_rdf_result_for_doc_with_invalid_dateofprintpublication(
    persee_rdf_graph_for_doc_with_invalid_dateofprintpublication,
) -> RdfHarvesterRawResult:
    """Rdf result from persee wrapped in a RdfHarvesterRawResult"""
    return RdfHarvesterRawResult(
        payload=persee_rdf_graph_for_doc_with_invalid_dateofprintpublication,
        source_identifier="http://data.persee.fr/doc/hista_0992-2059_1998_num_42_1_2826#Web",
        formatter_name=IdrefHarvester.Formatters.PERSEE_RDF.value,
    )


@pytest.fixture(name="persee_rdf_graph_for_doc_with_invalid_dateofprintpublication")
def fixture_persee_rdf_graph_for_doc_with_invalid_dateofprintpublication(
    _base_path,
) -> Graph:
    """Rdf graph from persee rdf file"""
    return _persee_rdf_graph_from_file(
        _base_path, "persee_document_with_invalid_dateofprintpublication"
    )


@pytest.fixture(name="persee_rdf_xml_for_hash_1")
def fixture_persee_rdf_xml_for_hash_1(_base_path) -> Graph:
    """Rdf graph from persee rdf file"""
    return _persee_rdf_graph_from_file(_base_path, "persee_document_for_hash_1")


@pytest.fixture(name="persee_rdf_xml_for_hash_2")
def fixture_persee_rdf_xml_for_hash_2(_base_path) -> Graph:
    """Rdf graph from persee rdf file"""
    return _persee_rdf_graph_from_file(_base_path, "persee_document_for_hash_2")


@pytest.fixture(name="persee_rdf_graph_for_person")
def fixture_persee_rdf_graph_for_person(_base_path) -> Graph:
    """Rdf graph from persee Person rdf file"""
    return _persee_rdf_graph_from_file(_base_path, "persee_person")


@pytest.fixture(name="persee_rdf_result_for_journal")
def fixture_persee_rdf_result_for_journal(_base_path) -> Graph:
    """Rdf graph from persee Journal rdf file"""
    return _persee_rdf_graph_from_file(_base_path, "persee_journal")


def _persee_rdf_graph_from_file(base_path, file_name) -> Graph:
    file_path = f"data/persee_rdf/{file_name}.rdf"
    return _rdf_graph_from_xml_file(base_path, file_path)


def _rdf_graph_from_xml_file(base_path, file_path) -> Graph:
    input_data = _rdf_xml_file_content(base_path, file_path)
    return Graph().parse(data=input_data, format="xml")


def _rdf_xml_file_content(base_path, file_path):
    file = pathlib.Path(base_path / file_path)
    with open(file, encoding="utf-8") as xml_file:
        return xml_file.read()
