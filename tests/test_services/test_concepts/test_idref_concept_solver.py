from unittest import mock

import aiohttp
import pytest

from app.config import get_app_settings
from app.db.models.concept import Concept as DbConcept
from app.services.concepts.concept_informations import ConceptInformations
from app.services.concepts.dereferencing_error import DereferencingError
from app.services.concepts.idref_concept_solver import IdRefConceptSolver


@pytest.fixture(name="mock_idref_concept_solver", autouse=True)
def fixture_mock_idref_concept_solver():
    """Disable mock for IdRefConceptSolver"""
    return


@pytest.fixture(name="idref_concept_http_client_mock")
def fixture_idref_concept_http_client_mock(idref_rdf_raw_result_for_concept: str):
    """Retrieval service mock to detect run method calls."""
    with mock.patch.object(aiohttp.ClientSession, "get") as aiohttp_client_session_get:
        aiohttp_client_session_get.return_value.__aenter__.return_value.status = 200
        aiohttp_client_session_get.return_value.__aenter__.return_value.text.return_value = (
            idref_rdf_raw_result_for_concept
        )
        yield aiohttp_client_session_get


@pytest.fixture(name="idref_multilang_concept_http_client_mock")
def fixture_idref_multilang_concept_http_client_mock(
    idref_rdf_raw_result_for_multilang_labels_concept: str,
):
    """Retrieval service mock to detect run method calls."""
    with mock.patch.object(aiohttp.ClientSession, "get") as aiohttp_client_session_get:
        aiohttp_client_session_get.return_value.__aenter__.return_value.status = 200
        aiohttp_client_session_get.return_value.__aenter__.return_value.text.return_value = (
            idref_rdf_raw_result_for_multilang_labels_concept
        )
        yield aiohttp_client_session_get


@pytest.fixture(name="idref_nolang_concept_http_client_mock")
def fixture_idref_nolang_concept_http_client_mock(
    idref_rdf_raw_result_for_no_lang_labels_concept: str,
):
    """Retrieval service mock to detect run method calls."""
    with mock.patch.object(aiohttp.ClientSession, "get") as aiohttp_client_session_get:
        aiohttp_client_session_get.return_value.__aenter__.return_value.status = 200
        aiohttp_client_session_get.return_value.__aenter__.return_value.text.return_value = (
            idref_rdf_raw_result_for_no_lang_labels_concept
        )
        yield aiohttp_client_session_get


@pytest.fixture(name="idref_non_preferred_lang_concept_http_client_mock")
def fixture_idref_non_preferred_lang_concept_http_client_mock(
    idref_rdf_raw_result_for_non_preferred_lang_labels_concept: str,
):
    """Retrieval service mock to detect run method calls."""
    with mock.patch.object(aiohttp.ClientSession, "get") as aiohttp_client_session_get:
        aiohttp_client_session_get.return_value.__aenter__.return_value.status = 200
        aiohttp_client_session_get.return_value.__aenter__.return_value.text.return_value = (
            idref_rdf_raw_result_for_non_preferred_lang_labels_concept
        )
        yield aiohttp_client_session_get


@pytest.mark.asyncio
async def test_idref_concept_solver_calls_url_from_uri(
    idref_rdf_raw_result_for_concept: str,
):
    """
    GIVEN an idref concept solver
    WHEN calling it with the concept id https://www.idref.fr/082303363/id
    THEN the URL https://www.idref.fr/082303363.rdf is called through aiohttp
    :return:
    """
    concept_uri = "https://www.idref.fr/082303363/id"
    with mock.patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value.status = 200
        mock_get.return_value.__aenter__.return_value.text.return_value = (
            idref_rdf_raw_result_for_concept
        )
        concept_informations = ConceptInformations(uri=concept_uri)
        solver = IdRefConceptSolver()
        solver.complete_information(concept_informations)
        await solver.solve(concept_informations)
        mock_get.assert_called_once_with("https://www.idref.fr/082303363.rdf")


@pytest.mark.asyncio
async def test_idref_concept_solver_calls_url_from_numeric_id(
    idref_rdf_raw_result_for_concept: str,
):
    """
    GIVEN an idref concept solver
    WHEN calling it with the concept id "082303363"
    THEN the URL https://www.idref.fr/082303363.rdf is called through aiohttp
    :return:
    """
    concept_id = "082303363"
    with mock.patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value.status = 200
        mock_get.return_value.__aenter__.return_value.text.return_value = (
            idref_rdf_raw_result_for_concept
        )
        concept_informations = ConceptInformations(
            code=concept_id, source=ConceptInformations.ConceptSources.IDREF
        )
        solver = IdRefConceptSolver()
        solver.complete_information(concept_informations)
        await solver.solve(concept_informations)
        mock_get.assert_called_once_with("https://www.idref.fr/082303363.rdf")


@pytest.mark.asyncio
async def test_idref_concept_solver_raises_value_error_with_fantasy_string():
    """
    GIVEN an idref concept solver
    WHEN calling it with the concept id "fantasy"
    THEN a Value error is raised with the message "Invalid idref concept id or uri {concept_id}"
    and the aiohttp client is not called
    :return:
    """
    concept_id = "fantasy"
    with mock.patch("aiohttp.ClientSession.get") as mock_get:
        with pytest.raises(DereferencingError) as exception_info:
            concept_informations = ConceptInformations(code=concept_id)
            solver = IdRefConceptSolver()
            solver.complete_information(concept_informations)
            await solver.solve(concept_informations)
        assert (
            exception_info.value.args[0]
            == f"Invalid idref concept id or uri http://www.idref.fr/{concept_id}/id"
        )
        mock_get.assert_not_called()


@pytest.mark.asyncio
async def test_idref_concept_solver_returns_db_concept(idref_concept_http_client_mock):
    """
    GIVEN an idref concept solver
    WHEN calling it with the concept id "082303363"
    THEN the returned value is a DbConcept with the correct uri and label
    :return:
    """
    concept_id = "082303363"
    concept_informations = ConceptInformations(code=concept_id)
    solver = IdRefConceptSolver()
    solver.complete_information(concept_informations)
    result = await solver.solve(concept_informations)
    idref_concept_http_client_mock.assert_called_once_with(
        "https://www.idref.fr/082303363.rdf"
    )
    assert result is not None
    assert isinstance(result, DbConcept)
    assert result.uri == "http://www.idref.fr/082303363/id"
    assert "Bouillabaisse" in [
        label.value
        for label in result.labels
        if label.language == "fr" and label.preferred
    ]


@pytest.mark.asyncio
async def test_idref_concept_solver_returns_concepts_in_preferred_language(
    idref_multilang_concept_http_client_mock,
):
    """
    GIVEN an idref concept solver and "fr", "en" as preferred languages
    WHEN calling it with the concept id "123456789" which has labels in several languages
    THEN the retured DbConcept has only labels in the preferred languages
    :return:
    """
    assert get_app_settings().concept_languages == ["fr", "en"]
    concept_id = "123456789"
    concept_informations = ConceptInformations(code=concept_id)
    solver = IdRefConceptSolver()
    solver.complete_information(concept_informations)
    result = await IdRefConceptSolver().solve(concept_informations)
    idref_multilang_concept_http_client_mock.assert_called_once_with(
        "https://www.idref.fr/123456789.rdf"
    )
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
    assert "French pref label" in [
        label.value
        for label in result.labels
        if label.language == "fr" and label.preferred
    ]
    assert "English preferred label" in [
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
    assert "English alternative label" in [
        label.value
        for label in result.labels
        if label.language == "en" and not label.preferred
    ]
    assert "Unspecified language alternative label" in [
        label.value
        for label in result.labels
        if label.language is None and not label.preferred
    ]


@pytest.mark.asyncio
async def test_idref_concept_solver_returns_concepts_without_language(
    idref_nolang_concept_http_client_mock,
):
    """
    GIVEN an idref concept solver and "fr", "en" as preferred languages
    WHEN calling it with the concept id "123456789" which has labels without languages
    THEN the retured DbConcept has labels without languages
    :return:
    """
    assert get_app_settings().concept_languages == ["fr", "en"]
    concept_id = "123456789"
    concept_informations = ConceptInformations(code=concept_id)
    solver = IdRefConceptSolver()
    solver.complete_information(concept_informations)
    result = await solver.solve(concept_informations)
    idref_nolang_concept_http_client_mock.assert_called_once_with(
        "https://www.idref.fr/123456789.rdf"
    )
    assert len(result.labels) == 2
    assert len([label for label in result.labels if label.preferred]) == 1
    assert len([label for label in result.labels if not label.preferred]) == 1
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
    assert "Unspecified language preferred label" in [
        label.value
        for label in result.labels
        if label.language is None and label.preferred
    ]
    assert "Unspecified language alternative label" in [
        label.value
        for label in result.labels
        if label.language is None and not label.preferred
    ]


@pytest.mark.asyncio
async def test_idref_concept_solver_returns_concepts_in_non_preferred_languages(
    idref_non_preferred_lang_concept_http_client_mock,
):
    """
    GIVEN an idref concept solver and "fr", "en" as preferred languages
    WHEN calling it with the concept id "123456789"
        which has only labels in languages that are not preferred
    THEN the retured DbConcept has 1 altlabel and 1 preflabel in any of the non preferred languages
    :return:
    """
    assert get_app_settings().concept_languages == ["fr", "en"]
    concept_id = "123456789"
    concept_informations = ConceptInformations(code=concept_id)
    solver = IdRefConceptSolver()
    solver.complete_information(concept_informations)
    result = await solver.solve(concept_informations)
    idref_non_preferred_lang_concept_http_client_mock.assert_called_once_with(
        "https://www.idref.fr/123456789.rdf"
    )
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
        "Русская предпочтительная метка",
        "Etiqueta preferida en español",
        "中文首选标签",
        "Türkçe tercih edilen etiket",
    ]
