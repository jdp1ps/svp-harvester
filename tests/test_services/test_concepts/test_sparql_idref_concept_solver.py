from unittest import mock

import aiosparql
import pytest

from app.config import get_app_settings
from app.db.models.concept import Concept as DbConcept
from app.services.concepts.concept_informations import ConceptInformations
from app.services.concepts.dereferencing_error import DereferencingError
from app.services.concepts.sparql_idref_concept_solver import SparqlIdRefConceptSolver


@pytest.fixture(name="mock_idref_concept_solver", autouse=True)
def fixture_mock_idref_concept_solver():
    """Disable mock for IdRefConceptSolver"""
    return


@pytest.fixture(name="idref_sparql_endpoint_client_mock_with_concept")
def fixture_idref_sparql_endpoint_client_mock_with_concept(
        idref_sparql_endpoint_response_for_concept: dict,
):
    """Retrieval service mock to detect run method calls."""
    with mock.patch.object(
            aiosparql.client.SPARQLClient, "query"
    ) as aiosparql_client_query:
        aiosparql_client_query.return_value = idref_sparql_endpoint_response_for_concept
        yield aiosparql_client_query


@pytest.fixture(name="idref_sparql_endpoint_client_mock_with_concept_multilang")
def fixture_idref_sparql_endpoint_client_mock_with_concept_multilang(
        idref_sparql_endpoint_response_for_concept_multilang: dict,
):
    """Retrieval service mock to detect run method calls."""
    with mock.patch.object(
            aiosparql.client.SPARQLClient, "query"
    ) as aiosparql_client_query:
        aiosparql_client_query.return_value = idref_sparql_endpoint_response_for_concept_multilang
        yield aiosparql_client_query


@pytest.fixture(name="idref_sparql_endpoint_client_mock_with_concept_non_preferred_languages")
def fixture_idref_sparql_endpoint_client_mock_with_concept_non_preferred_languages(
        idref_sparql_endpoint_response_for_concept_non_preferred_languages: dict,
):
    """Retrieval service mock to detect run method calls."""
    with mock.patch.object(
            aiosparql.client.SPARQLClient, "query"
    ) as aiosparql_client_query:
        aiosparql_client_query.return_value = (
            idref_sparql_endpoint_response_for_concept_non_preferred_languages
        )
        yield aiosparql_client_query


@pytest.mark.asyncio
async def test_idref_concept_solver_raises_value_error_with_fantasy_string(
        idref_sparql_endpoint_client_mock_with_concept
):
    """
    GIVEN an idref concept solver
    WHEN calling it with the concept id "fantasy"
    THEN a Value error is raised with the message "Invalid idref concept id or uri {concept_id}"
    and the aiohttp client is not called
    :return:
    """
    concept_id = "fantasy"
    with pytest.raises(DereferencingError) as exception_info:
        concept_informations = ConceptInformations(code=concept_id)
        solver = SparqlIdRefConceptSolver()
        solver.complete_information(concept_informations)
        await solver.solve(concept_informations)
    assert (
            exception_info.value.args[0]
            == f"Invalid idref concept id or uri http://www.idref.fr/{concept_id}/id"
    )
    idref_sparql_endpoint_client_mock_with_concept.assert_not_called()


@pytest.mark.asyncio
async def test_idref_concept_solver_return_db_concept_from_uri(
        idref_sparql_endpoint_client_mock_with_concept
):
    """
    GIVEN an idref concept solver
    WHEN calling it with the concept id https://www.idref.fr/027231313/id
    THEN the returned value is a DbConcept with the correct uri and label
    :return:
    """
    concept_uri = "https://www.idref.fr/027231313/id"
    concept_informations = ConceptInformations(uri=concept_uri)
    solver = SparqlIdRefConceptSolver()
    solver.complete_information(concept_informations)
    result = await solver.solve(concept_informations)
    idref_sparql_endpoint_client_mock_with_concept.assert_called_once()
    assert result
    assert isinstance(result, DbConcept)
    assert result.uri == "http://www.idref.fr/027231313/id"
    assert "Cuisine" in [
        label.value
        for label in result.labels
        if label.language == "fr" and label.preferred
    ]
    assert "Recettes de cuisine" in [
        label.value
        for label in result.labels
        if not label.preferred and not label.language
    ]


@pytest.mark.asyncio
async def test_idref_concept_solver_returns_db_concept_from_numeric_id(
        idref_sparql_endpoint_client_mock_with_concept # pylint: disable=unused-argument
):
    """
    GIVEN an idref concept solver
    WHEN calling it with the concept id "027231313"
    THEN the returned value is a DbConcept with the correct uri and label
    :return:
    """
    concept_id = "027231313"
    concept_informations = ConceptInformations(code=concept_id)
    solver = SparqlIdRefConceptSolver()
    solver.complete_information(concept_informations)
    result = await solver.solve(concept_informations)
    assert result is not None
    assert isinstance(result, DbConcept)
    assert result.uri == "http://www.idref.fr/027231313/id"
    assert "Cuisine" in [
        label.value
        for label in result.labels
        if label.language == "fr" and label.preferred
    ]


@pytest.mark.asyncio
async def test_idref_concept_solver_return_db_concept_from_numeric_id_and_source(
        idref_sparql_endpoint_client_mock_with_concept
):
    """
    GIVEN an idref concept solver
    WHEN calling it with the concept id "027231313"
    THEN the returned value is a DbConcept with the correct uri and label
    :return:
    """
    concept_id = "027231313"
    concept_informations = ConceptInformations(
        code=concept_id, source=ConceptInformations.ConceptSources.IDREF
    )
    solver = SparqlIdRefConceptSolver()
    solver.complete_information(concept_informations)
    result = await solver.solve(concept_informations)
    idref_sparql_endpoint_client_mock_with_concept.assert_called_once()
    assert result
    assert result.uri == "http://www.idref.fr/027231313/id"


@pytest.mark.asyncio
async def test_idref_concept_solver_returns_concepts_in_preferred_language(
        idref_sparql_endpoint_client_mock_with_concept_multilang,
):
    """
    GIVEN an idref concept solver and "fr", "en" as preferred languages
    WHEN calling it with the concept id "027231313" which has labels in several languages
    THEN the retured DbConcept has only labels in the preferred languages
    :return:
    """
    assert get_app_settings().concept_languages == ["fr", "en"]
    concept_id = "027231313"
    concept_informations = ConceptInformations(code=concept_id)
    solver = SparqlIdRefConceptSolver()
    solver.complete_information(concept_informations)
    result = await SparqlIdRefConceptSolver().solve(concept_informations)
    idref_sparql_endpoint_client_mock_with_concept_multilang.assert_called_once()
    assert len(result.labels) == 5
    # 3 preflabels, one in french, one in english, one in unspecified language
    assert len([label for label in result.labels if label.preferred]) == 3
    assert (
            len(
                [
                    label
                    for label in result.labels
                    if label.language == "fr" and label.preferred
                ]
            )
            == 1
    )
    assert (
            len(
                [
                    label
                    for label in result.labels
                    if label.language == "en" and label.preferred
                ]
            )
            == 1
    )
    assert (
            len(
                [
                    label
                    for label in result.labels
                    if label.language is None and label.preferred
                ]
            )
            == 1
    )
    assert "Cuisine" in [
        label.value
        for label in result.labels
        if label.language == "fr" and label.preferred
    ]
    assert "Kitchen" in [
        label.value
        for label in result.labels
        if label.language == "en" and label.preferred
    ]
    assert "Unspecified language preferred label" in [
        label.value
        for label in result.labels
        if label.language is None and label.preferred
    ]
    # 2 altlabels, one in english, one in unspecified language
    assert len([label for label in result.labels if not label.preferred]) == 2
    assert (
            len(
                [
                    label
                    for label in result.labels
                    if label.language == "en" and not label.preferred
                ]
            )
            == 1
    )
    assert (
            len(
                [
                    label
                    for label in result.labels
                    if label.language is None and not label.preferred
                ]
            )
            == 1
    )
    assert "Culinary art" in [
        label.value
        for label in result.labels
        if label.language == "en" and not label.preferred
    ]
    assert "Art culinaire" in [
        label.value
        for label in result.labels
        if label.language is None and not label.preferred
    ]


@pytest.mark.asyncio
async def test_idref_concept_solver_returns_concepts_in_non_preferred_languages(
        idref_sparql_endpoint_client_mock_with_concept_non_preferred_languages,
):
    """
    GIVEN an idref concept solver and "fr", "en" as preferred languages
    WHEN calling it with the concept id "027231313"
        which has only labels in languages that are not preferred
    THEN the retured DbConcept has 1 preflabel in any of the non preferred languages
    :return:
    """
    assert get_app_settings().concept_languages == ["fr", "en"]
    concept_id = "027231313"
    concept_informations = ConceptInformations(code=concept_id)
    solver = SparqlIdRefConceptSolver()
    solver.complete_information(concept_informations)
    result = await solver.solve(concept_informations)
    idref_sparql_endpoint_client_mock_with_concept_non_preferred_languages.assert_called_once()
    assert len(result.labels) == 1
    assert len([label for label in result.labels if label.preferred]) == 1
    assert len([label for label in result.labels if not label.preferred]) == 0
    assert (
            len(
                [
                    label
                    for label in result.labels
                    if label.language is not None and label.preferred
                ]
            )
            == 1
    )
    assert (
            len(
                [
                    label
                    for label in result.labels
                    if label.language is not None and not label.preferred
                ]
            )
            == 0
    )
    assert result.labels[0].value in [
        "Cucina",
        "Cocina",
    ]
