"""Test the references API."""
from unittest import mock

from fastapi import HTTPException
import pytest

from app.db.models.retrieval import Retrieval
from app.harvesters.hal.hal_harvester import HalHarvester
from app.harvesters.idref.idref_harvester import IdrefHarvester
from app.harvesters.scanr.scanr_harvester import ScanrHarvester
from app.harvesters.open_alex.open_alex_harvester import OpenAlexHarvester
from app.models.identifiers import Identifier
from app.models.people import Person
from app.services.retrieval.retrieval_service import RetrievalService


def test_retrieval_service_build_harvesters():
    """Test that the retrieval service builds the expected harvesters from the yml settings."""
    service = RetrievalService()
    service._build_harvesters()  # pylint: disable=protected-access
    assert len(service.harvesters) == 4
    assert "hal" in service.harvesters
    assert "idref" in service.harvesters
    assert "scanr" in service.harvesters
    assert "openalex" in service.harvesters
    assert isinstance(service.harvesters["hal"], HalHarvester)
    assert isinstance(service.harvesters["idref"], IdrefHarvester)
    assert isinstance(service.harvesters["scanr"], ScanrHarvester)
    assert isinstance(service.harvesters["openalex"], OpenAlexHarvester)


def test_retrieval_service_with_limited_harvesters():
    """Test that the retrieval service builds the expected harvesters from the yml settings."""
    service = RetrievalService(harvesters=["hal"])
    service._build_harvesters()  # pylint: disable=protected-access
    assert len(service.harvesters) == 1
    assert "hal" in service.harvesters
    assert isinstance(service.harvesters["hal"], HalHarvester)


@pytest.mark.asyncio
async def test_retrieval_service_returns_retrieval_for_person(
    person_with_name_and_idref: Person,
):
    """
    GIVEN a retrieval service
    WHEN registering a person
    THEN a retrieval is returned with the person as entity

    :param person_with_name_and_idref:
    :return:
    """
    service = RetrievalService()
    retrieval: Retrieval = await service.register(person_with_name_and_idref)
    assert retrieval.entity.name == person_with_name_and_idref.name
    assert retrieval.entity.get_identifier(
        "idref"
    ) == person_with_name_and_idref.get_identifier("idref")


@pytest.fixture(name="mock_hal_harvester_is_relevant")
def fixture_mock_hal_harvester_is_relevant():
    """Hal harvester mock to detect is_relevant method calls."""
    with mock.patch.object(HalHarvester, "is_relevant") as mock_is_relevant:
        yield mock_is_relevant


@pytest.mark.asyncio
async def test_retrieval_service_registers_identifiers_matches(
    person_with_name_and_id_hal_s: Person, mock_hal_harvester_is_relevant
):
    """
    GIVEN a retrieval service to which a person with one identifier has been submitted
    WHEN registering the same person with only one identifier
    THEN it launches the retrieval with the two identifiers
    :param person_with_name_and_id_hal_s:
    :return:
    """
    # add orcid identifier ro person_with_name_and_id_hal_s

    orcid_identifier = Identifier(
        type="orcid",
        value="0000-0002-1825-0097",
    )
    person_with_name_and_id_hal_s.identifiers.append(orcid_identifier)
    service = RetrievalService()
    await service.register(person_with_name_and_id_hal_s)
    # remove orcid identifier ro person_with_name_and_id_hal_s
    person_with_name_and_id_hal_s.identifiers.pop()
    retrieval: Retrieval = await service.register(person_with_name_and_id_hal_s)
    assert retrieval.entity.name == person_with_name_and_id_hal_s.name
    assert retrieval.entity.get_identifier(
        "idref"
    ) == person_with_name_and_id_hal_s.get_identifier("idref")
    assert retrieval.entity.get_identifier("orcid") == orcid_identifier.value
    assert len(retrieval.entity.identifiers) == 2
    await service.run()
    mock_hal_harvester_is_relevant.assert_called_once()
    hal_harvester_args, _ = mock_hal_harvester_is_relevant.call_args
    assert len(hal_harvester_args[0].identifiers) == 2
    assert hal_harvester_args[0].get_identifier(
        "idref"
    ) == person_with_name_and_id_hal_s.get_identifier("idref")
    assert hal_harvester_args[0].get_identifier("orcid") == orcid_identifier.value


@pytest.mark.asyncio
async def test_retrieval_service_registers_identifiers_matches_nullify(
    person_with_name_and_id_hal_s: Person,
):
    """
    GIVEN a retrieval service
    WHEN registering a person
    THEN a retrieval is returned with the person as entity

    :param person_with_name_and_id_hal_s:
    :return:
    """
    service = RetrievalService(nullify=["id_hal_s"])

    with pytest.raises(HTTPException) as exc_info:
        await service.register(person_with_name_and_id_hal_s)

    assert exc_info.value.status_code == 422
    assert (
        exc_info.value.detail
        == "Unprocessable Entity: id_hal_s cannot be declared and nullified at same time"
    )



@pytest.mark.asyncio
async def test_retrieval_service_idref_with_invalid_idref_format(
        person_with_name_and_invalid_idref: Person,
        caplog,
        mock_handle_error,
):
    """
    GIVEN a retrieval service to which a person with an invalid idref has been submitted
    WHEN running the RetrievalService
    THEN a warning should be logged and handle_error should be called
    :param person_with_name_and_invalid_idref:
    :return:
    """

    service = RetrievalService(harvesters=["idref"])
    await service.register(person_with_name_and_invalid_idref)
    retrieval: Retrieval = await service.register(person_with_name_and_invalid_idref)
    await service.run()
    assert "Unexpected idref format detected" in caplog.text
    assert mock_handle_error.call_count == 1


@pytest.mark.asyncio
async def test_retrieval_service_idref_with_invalid_idref_and_valid_orcid_format(
        person_with_name_and_invalid_idref: Person,
        caplog,
        mock_handle_error,
):
    """
    GIVEN a retrieval service to which a person with an invalid idref has been submitted
    WHEN running the RetrievalService
    THEN a warning should be logged but handle_error should not be called
    :param person_with_name_and_invalid_idref:
    :return:
    """

    orcid_identifier = Identifier(
        type="orcid",
        value="0000-0002-1825-0097",
    )
    person_with_name_and_invalid_idref.identifiers.append(orcid_identifier)
    service = RetrievalService(harvesters=["idref"])
    await service.register(person_with_name_and_invalid_idref)
    retrieval: Retrieval = await service.register(person_with_name_and_invalid_idref)
    await service.run()
    assert "Unexpected idref format detected" in caplog.text
    assert mock_handle_error.call_count == 0
