import datetime
from unittest import mock

import aiosparql.client
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.harvesters.idref.idref_harvester import IdrefHarvester
from app.harvesters.idref.idref_references_converter import IdrefReferencesConverter
from app.models.references import Reference


@pytest.fixture(name="idref_sparql_endpoint_client_mock_with_idref_pubs")
def fixture_idref_sparql_endpoint_client_mock_with_idref_pubs(
    idref_sparql_endpoint_results_with_idref_pubs: dict,
):
    """Retrieval service mock to detect run method calls."""
    with mock.patch.object(
        aiosparql.client.SPARQLClient, "query"
    ) as aiosparql_client_query:
        aiosparql_client_query.return_value = (
            idref_sparql_endpoint_results_with_idref_pubs
        )
        yield aiosparql_client_query


@pytest.fixture(name="idref_sparql_endpoint_client_mock_with_sudoc_pub")
def fixture_idref_sparql_endpoint_client_mock_with_sudoc_pub(
    idref_sparql_endpoint_results_with_sudoc_pub: dict,
):
    """Retrieval service mock to detect run method calls."""
    with mock.patch.object(
        aiosparql.client.SPARQLClient, "query"
    ) as aiosparql_client_query:
        aiosparql_client_query.return_value = (
            idref_sparql_endpoint_results_with_sudoc_pub
        )
        yield aiosparql_client_query


@pytest.mark.integration
@pytest.mark.asyncio
async def test_idref_harvester_finds_doc(
    harvesting_db_model_for_person_with_idref,
    reference_recorder_register_mock,
    idref_sparql_endpoint_client_mock_with_idref_pubs,  # pylint: disable=unused-argument
    async_session: AsyncSession,
):
    """Test that the harvester will find documents."""
    harvester = IdrefHarvester(converter=IdrefReferencesConverter())
    async_session.add(harvesting_db_model_for_person_with_idref)
    await async_session.commit()
    harvester.set_harvesting_id(harvesting_db_model_for_person_with_idref.id)
    harvester.set_entity_id(
        harvesting_db_model_for_person_with_idref.retrieval.entity_id
    )
    await harvester.run()
    idref_sparql_endpoint_client_mock_with_idref_pubs.assert_called_once()
    reference_recorder_register_mock.assert_called_once()
    _, arg = reference_recorder_register_mock.call_args
    reference: Reference = arg["new_ref"]
    assert len(reference.titles) == 1
    assert (
        reference.titles[0].value
        == "Ressources mondialisées, Essais de géographie politique"
    )
    assert reference.titles[0].language == "fr"
    assert len(reference.abstracts) == 1
    assert (
        reference.abstracts[0].value
        == "La société 2.0 qui fait l'air du temps mondialisé ne se réduit pas "
        "à l'information numérique et aux flux immatériels."
    )
    assert len(reference.subjects) == 3
    assert any(
        subject.uri == "http://www.idref.fr/027732428/id"
        and any(
            label.language == "fr" and label.value == "Géopolitique"
            for label in subject.labels
        )
        for subject in reference.subjects
    )
    assert reference.issued == datetime.date(2011, 1, 1)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_idref_harvester_finds_sudoc_doc(
    harvesting_db_model_for_person_with_idref,
    reference_recorder_register_mock,
    idref_sparql_endpoint_client_mock_with_sudoc_pub,  # pylint: disable=unused-argument
    async_session: AsyncSession,
):
    """Test that the harvester will find documents."""
    harvester = IdrefHarvester(converter=IdrefReferencesConverter())
    async_session.add(harvesting_db_model_for_person_with_idref)
    await async_session.commit()
    harvester.set_harvesting_id(harvesting_db_model_for_person_with_idref.id)
    harvester.set_entity_id(
        harvesting_db_model_for_person_with_idref.retrieval.entity_id
    )
    await harvester.run()
    idref_sparql_endpoint_client_mock_with_sudoc_pub.assert_called_once()
    reference_recorder_register_mock.assert_called_once()
    _, arg = reference_recorder_register_mock.call_args
    reference: Reference = arg["new_ref"]
    assert len(reference.titles) == 2
    assert (
        reference.titles[0].value
        == "Agriculture des métropoles  : voie d'avenir ou cache-misère ?"
    )
    assert reference.titles[0].language is None
    expected_french_abstract_beginning = (
        "Le présent dossier aborde la participation de cette agriculture urbaine "
    )
    assert len(reference.abstracts) == 1
    assert reference.abstracts[0].value.startswith(expected_french_abstract_beginning)
