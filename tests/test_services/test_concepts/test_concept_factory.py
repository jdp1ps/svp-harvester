from unittest import mock

import pytest

from app.config import get_app_settings
from app.services.concepts.concept_factory import ConceptFactory
from app.services.concepts.concept_informations import ConceptInformations
from app.services.concepts.sparql_idref_concept_solver import SparqlIdRefConceptSolver
from app.services.concepts.skosmos_jel_concept_solver import SkosmosJelConceptSolver
from app.services.concepts.sparql_jel_concept_solver import SparqlJelConceptSolver
from app.services.concepts.unknown_authority_exception import UnknownAuthorityException
from app.services.concepts.wikidata_concept_solver import WikidataConceptSolver


@pytest.fixture(name="mock_idref_concept_solver_solve")
def fixture_mock_idref_concept_solver_solve():
    """
    Mocks the IdRefConceptSolver.solve method
    :return: mock
    """
    with mock.patch.object(SparqlIdRefConceptSolver, "solve") as mock_solve:
        yield mock_solve


@pytest.fixture(name="mock_wikidata_concept_solver_solve")
def fixture_mock_wikidata_concept_solver_solve():
    """
    Mocks the WikidataConceptSolver.solve method
    :return: mock
    """
    with mock.patch.object(WikidataConceptSolver, "solve") as mock_solve:
        yield mock_solve


@pytest.fixture(name="mock_jel_concept_solver_solve")
def fixture_mock_jel_concept_solver_solve():
    """
    Mocks the SkosmosJelConceptSolver.solve method
    :return: mock
    """
    with mock.patch.object(SkosmosJelConceptSolver, "solve") as mock_solve:
        yield mock_solve


@pytest.fixture(name="mock_sparql_jel_concept_solver_solve")
def fixture_mocksparql__jel_concept_solver_solve():
    """
    Mocks the SkosmosJelConceptSolver.solve method
    :return: mock
    """
    with mock.patch.object(SparqlJelConceptSolver, "solve") as mock_solve:
        yield mock_solve


# if we call the concept factory with a concept id beginning with http://www.idref.fr,
# without specifying a source,  then the idref solver is called
@pytest.mark.asyncio
async def test_concept_factory_idref_concept_uri(mock_idref_concept_solver_solve):
    """
    GIVEN a concept factory
    WHEN calling it with a concept id beginning with http://www.idref.fr
    THEN the idref concept solver is called
    :param mock_idref_concept_solver_solve:
    :return:
    """
    concept_code = "033265077"
    concept_uri = "http://www.idref.fr/033265077/id"
    concept_url = "https://www.idref.fr/033265077.rdf"
    concept_informations = ConceptInformations(uri=concept_uri)
    ConceptFactory.complete_information(concept_informations)
    await ConceptFactory.solve(concept_informations)
    mock_idref_concept_solver_solve.assert_called_once()
    args, _ = mock_idref_concept_solver_solve.call_args
    assert args[0].uri == concept_uri
    assert args[0].code == concept_code
    assert args[0].url == concept_url


# if we call the concept factory with a concept number and specifying the idref source,
# then the idref solver is called
@pytest.mark.asyncio
async def test_concept_factory_idref_concept_number(mock_idref_concept_solver_solve):
    """
    GIVEN a concept factory
    WHEN calling it with a concept number and specifying the idref source
    THEN the idref concept solver is called
    :param mock_idref_concept_solver_solve:
    :return:
    """
    concept_code = "033265077"
    concept_uri = "http://www.idref.fr/033265077/id"
    concept_url = "https://www.idref.fr/033265077.rdf"
    concept_informations = ConceptInformations(
        code=concept_code, source=ConceptInformations.ConceptSources.IDREF
    )
    ConceptFactory.complete_information(concept_informations)
    await ConceptFactory.solve(concept_informations)
    mock_idref_concept_solver_solve.assert_called_once()
    args, _ = mock_idref_concept_solver_solve.call_args
    assert args[0].uri == concept_uri
    assert args[0].code == concept_code
    assert args[0].url == concept_url


# if we call the concept factory with a concept number and specifying the wikidata source,
# then the wikidata solver is called
@pytest.mark.asyncio
async def test_concept_factory_wikidata_concept_number(
    mock_wikidata_concept_solver_solve,
):
    """
    GIVEN a concept factory
    WHEN calling it with a concept number and specifying the wikidata source
    THEN the wikidata concept solver is called
    :param mock_wikidata_concept_solver_solve:
    :return:
    """
    concept_code = "Q1234"
    concept_uri = "http://www.wikidata.org/entity/Q1234"
    concept_url = "https://www.wikidata.org/wiki/Special:EntityData/Q1234.json"
    concept_informations = ConceptInformations(
        code=concept_code, source=ConceptInformations.ConceptSources.WIKIDATA
    )
    ConceptFactory.complete_information(concept_informations)
    await ConceptFactory.solve(concept_informations)
    mock_wikidata_concept_solver_solve.assert_called_once()
    args, _ = mock_wikidata_concept_solver_solve.call_args
    assert args[0].uri == concept_uri
    assert args[0].code == concept_code
    assert args[0].url == concept_url


@pytest.mark.asyncio
async def test_concept_factory_wikidata_concept_uri(mock_wikidata_concept_solver_solve):
    """
    GIVEN a concept factory
    WHEN calling it with a concept uri beginning with http://www.wikidata.org
            without specifying a source,
    THEN the wikidata concept solver is called
    :param mock_wikidata_concept_solver_solve:
    :return:
    """
    concept_code = "Q1234"
    concept_uri = "http://www.wikidata.org/entity/Q1234"
    concept_url = "https://www.wikidata.org/wiki/Special:EntityData/Q1234.json"
    concept_informations = ConceptInformations(uri=concept_uri)
    ConceptFactory.complete_information(concept_informations)
    await ConceptFactory.solve(concept_informations)
    mock_wikidata_concept_solver_solve.assert_called_once()
    args, _ = mock_wikidata_concept_solver_solve.call_args
    assert args[0].uri == concept_uri
    assert args[0].code == concept_code
    assert args[0].url == concept_url


@pytest.mark.asyncio
async def test_concept_factory_jel_concept_uri(mock_jel_concept_solver_solve):
    """
    GIVEN a concept factory
    WHEN calling it with a concept id beginning with http://zbw.eu/
    THEN the jel concept solver is called
    """
    settings = get_app_settings()
    settings.svp_jel_proxy_url = None
    concept_code = "A10"
    concept_uri = "http://zbw.eu/beta/external_identifiers/jel#A10"
    concept_url = (
        "https://zbw.eu/beta/skosmos/rest/v1/jel/data?"
        "uri=http%3A//zbw.eu/beta/external_identifiers/jel%23A10&format=application/rdf%2Bxml"
    )
    concept_informations = ConceptInformations(
        uri=concept_uri, source=ConceptInformations.ConceptSources.JEL
    )
    ConceptFactory.complete_information(concept_informations)
    await ConceptFactory.solve(concept_informations)
    mock_jel_concept_solver_solve.assert_called_once()
    args, _ = mock_jel_concept_solver_solve.call_args
    assert args[0].uri == concept_uri
    assert args[0].code == concept_code
    assert args[0].url == concept_url


@pytest.mark.asyncio
async def test_concept_factory_jel_concept_id(mock_jel_concept_solver_solve):
    """
    GIVEN a concept factory
    WHEN calling it with a concept id beginning with http://zbw.eu
    THEN the jel concept solver is called
    """
    settings = get_app_settings()
    settings.svp_jel_proxy_url = None
    concept_code = "A10"
    concept_uri = "http://zbw.eu/beta/external_identifiers/jel#A10"
    concept_informations = ConceptInformations(
        code=concept_code, source=ConceptInformations.ConceptSources.JEL
    )
    ConceptFactory.complete_information(concept_informations)
    await ConceptFactory.solve(concept_informations)
    mock_jel_concept_solver_solve.assert_called_once()
    args, _ = mock_jel_concept_solver_solve.call_args
    assert args[0].uri == concept_uri
    assert args[0].code == concept_code


@pytest.mark.asyncio
async def test_concept_factory_mock_sparkl_jel_concept_id(
    mock_sparql_jel_concept_solver_solve,
):
    """
    GIVEN a concept factory
    WHEN calling it with a concept id beginning with http://zbw.eu
    THEN the jel concept solver is called
    """
    settings = get_app_settings()
    settings.svp_jel_proxy_url = "http://fake_url"
    concept_code = "A10"
    concept_uri = "http://zbw.eu/beta/external_identifiers/jel#A10"
    concept_informations = ConceptInformations(uri=concept_uri)
    ConceptFactory.complete_information(concept_informations)
    await ConceptFactory.solve(concept_informations)
    mock_sparql_jel_concept_solver_solve.assert_called_once()
    args, _ = mock_sparql_jel_concept_solver_solve.call_args
    assert args[0].uri == concept_uri
    assert args[0].code == concept_code


# if we call the concept factory with a fake concept id, UnknownAuthorityException is raised
@pytest.mark.asyncio
async def test_concept_factory_unknown_authority_exception():
    """
    GIVEN a concept factory
    WHEN calling it with a fake concept id
    THEN UnknownAuthorityException is raised
    :return:
    """
    concept_uri = "http://www.fake.fr/033265077"
    with pytest.raises(UnknownAuthorityException):
        await ConceptFactory.solve(ConceptInformations(uri=concept_uri))
