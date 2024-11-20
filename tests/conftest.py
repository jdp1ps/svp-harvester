import asyncio
from os import environ
from typing import AsyncGenerator
from unittest import mock

from pytest import LogCaptureFixture
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient
from loguru import logger
from app.db.models.concept import Concept as DbConcept
from app.db.session import engine, Base
from app.services.concepts.abes_concept_solver import AbesConceptSolver
from app.services.concepts.concept_informations import ConceptInformations
from app.services.concepts.dereferencing_error import DereferencingError
from app.services.concepts.sparql_idref_concept_solver import SparqlIdRefConceptSolver
from app.harvesters.scanr.scanr_elastic_client import ScanRElasticClient
from app.services.concepts.sparql_jel_concept_solver import SparqlJelConceptSolver
from tests.fixtures.common import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.pydantic_entity_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.db_entity_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.hal_api_docs_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.idref_concept_rdf_docs_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.scanr_api_docs_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.science_plus_rdf_docs_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.idref_person_rdf_docs_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.sudoc_rdf_docs_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.idref_sparql_endpoint_docs_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.jel_sparql_endpoint_concepts_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.retrieval_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.harvesting_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.redis_cache_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.reference_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.reference_event_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.open_edition_doc_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.open_alex_docs_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.persee_rdf_docs_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.wikidata_concept_solver import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.organizations_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.rdf_resolver import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.scopus_docs_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import

environ["APP_ENV"] = "TEST"


@pytest.fixture(name="test_app")
def app() -> FastAPI:
    """Provide app as fixture"""
    # pylint: disable=import-outside-toplevel
    from app.main import SvpHarvester  # local import for testing purpose

    return SvpHarvester()


@pytest.fixture(name="test_client")
def fixture_test_client(test_app: FastAPI) -> TestClient:
    """Provide test client as fixture"""
    return TestClient(test_app)


@pytest.fixture(autouse=True, name="event_loop")
def fixture_event_loop():
    """Provide an event loop for all tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True, name="async_session")
async def fixture_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async db session for all tests"""
    session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session() as test_session:
        async with engine.begin() as test_connexion:
            await test_connexion.run_sync(Base.metadata.create_all)

        yield test_session

    async with engine.begin() as test_connexion:
        await test_connexion.run_sync(Base.metadata.drop_all)

    await engine.dispose()


def fake_idref_concept_solver(
    concept_informations: ConceptInformations,
):
    """
    Fake idref concept solver for tests
    Raises DereferencingError except for a specific concept id

    :param concept_id: concept id to solve
    :return: fake concept
    """
    if concept_informations.uri == "http://www.idref.fr/123456789X/id":
        return DbConcept(
            uri="http://www.idref.fr/123456789X/id",
            labels=[
                Label(
                    value="Idref concept allowed for test",
                    language="en",
                    preferred=True,
                ),
                Label(
                    value="Concept Idref autorisé pour les tests",
                    language="fr",
                    preferred=True,
                ),
                Label(
                    value="Idref concept you can use for tests",
                    language="en",
                    preferred=False,
                ),
                Label(
                    value="Concept Idref que vous pouvez utiliser pour les tests",
                    language="fr",
                    preferred=False,
                ),
            ],
        )

    raise DereferencingError("Idref concept dereferencing not allowed during tests")


def fake_jel_sparql_concept_solver(concept_id: str):
    """
    Fake Jel sparql concept solver for tests
    Raises DereferencingError except for a specific concept id

    :param concept_id: concept id to solve
    :return: fake concept
    """
    if concept_id == "http://zbw.eu/beta/external_identifiers/jel#TEST":
        return DbConcept(
            uri="http://zbw.eu/beta/external_identifiers/jel#TEST",
            labels=[
                Label(value="Test concept", language="en", preferred=True),
                Label(value="Concept de test", language="fr", preferred=True),
                Label(value="Test concept alternative", language="en", preferred=False),
                Label(
                    value="Concept de test alternatif", language="fr", preferred=False
                ),
            ],
        )
    raise DereferencingError("Jel concept dereferencing not allowed during tests")


def fake_idref_concept_uri_solver(concept_informations: ConceptInformations):
    """
    Fake idref concept solver for tests

    :param concept_id: concept id to solve
    :return: fake uri
    """
    pass


def fake_abes_concept_solver(concept_informations: ConceptInformations):
    """
    Fake abes concept solver for tests

    :param concept_id: concept id to solve
    :return: fake uri
    """
    if (
        str(concept_informations.uri)
        == "http://hub.abes.fr/cairn/periodical/autr/2024/issue_autr001/t35t/subject/test"
    ):
        return DbConcept(
            uri="http://hub.abes.fr/cairn/periodical/autr/2024/issue_autr001/t35t/subject/test",
            labels=[
                Label(
                    value="Idref concept allowed for test",
                    language="en",
                ),
                Label(
                    value="Concept Idref autorisé pour les tests",
                    language="fr",
                ),
            ],
        )

    raise DereferencingError("Abes concept dereferencing not allowed during tests")


@pytest.fixture(name="mock_idref_concept_solver", autouse=True)
def fixture_mock_idref_concept_solver():
    """Hal harvester mock to detect is_relevant method calls."""
    with mock.patch.object(SparqlIdRefConceptSolver, "solve") as mock_solve:
        mock_solve.side_effect = fake_idref_concept_solver
        yield mock_solve


@pytest.fixture(name="mock_sparql_jel_concept_solver", autouse=True)
def fixture_mock_sparql_jel_concept_solver():
    """Hal harvester mock to detect is_relevant method calls."""
    with mock.patch.object(SparqlJelConceptSolver, "solve") as mock_solve:
        mock_solve.side_effect = fake_jel_sparql_concept_solver
        yield mock_solve


@pytest.fixture(name="mock_abes_concept_solver", autouse=True)
def fixture_mock_abes_concept_solver():
    """abes harvester mock to detect is_relevant method calls."""
    with mock.patch.object(AbesConceptSolver, "solve") as mock_solve:
        mock_solve.side_effect = fake_abes_concept_solver
        yield mock_solve


@pytest.fixture(name="fake_scanr_elastic_client_perform_search")
def fixture_fake_scanr_elastic_client_perform_search(
    scanr_api_docs_from_publication,
    scanr_api_docs_from_person,
):
    async def fake_scanr_elastic_client(
        selected_index: str,
        base_size: int = 200,
    ):
        if selected_index == ScanRElasticClient.Indexes.PUBLICATIONS:
            for hit in scanr_api_docs_from_publication.get("hits", {}).get("hits", []):
                yield hit
        elif selected_index == ScanRElasticClient.Indexes.PERSONS:
            yield scanr_api_docs_from_person
        else:
            raise DereferencingError("Invalid index requested")

    return fake_scanr_elastic_client


@pytest.fixture(name="mock_scanr_elastic_client", autouse=True)
def fixture_mock_scanr_elastic_client(fake_scanr_elastic_client_perform_search):
    """Scanr harvester mock to detect is_relevant method calls."""
    with mock.patch.object(ScanRElasticClient, "perform_search") as mock_solve:
        mock_solve.side_effect = fake_scanr_elastic_client_perform_search
        yield mock_solve


@pytest.fixture(autouse=True)
def caplog(caplog: LogCaptureFixture):  # pylint: disable=redefined-outer-name
    """
    Make pytest work with loguru. See:
    https://loguru.readthedocs.io/en/stable/resources/migration.html#making-things-work-with-pytest-and-caplog
    :param caplog: pytest fixture
    :return: loguru compatible caplog
    """
    handler_id = logger.add(
        caplog.handler,
        format="{message}",
        level=0,
        filter=lambda record: record["level"].no >= caplog.handler.level,
        enqueue=False,
    )
    yield caplog
    try:
        logger.remove(handler_id)
    except ValueError:
        pass
