"""Test that references API creates Retrieval in database."""
from unittest import mock

import aiohttp
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration

REFERENCES_RETRIEVAL_API_PATH = "/api/v1/references/retrieval"
REFERENCE_EVENTS_API_PATH = "/api/v1/reference_events"


@pytest.mark.asyncio
async def test_fetch_references_contributions_history(  # pylint: disable=too-many-statements, too-many-locals
    test_client: TestClient,
    person_with_name_and_id_hal_i_json,
    hal_api_docs_with_contributors_version_1,
    hal_api_docs_with_contributors_version_2,
):
    """
    Test two requests with various changes in contributors taking place between the two requests.


    :param test_client:
    :param person_with_name_and_id_hal_i_json:
    :param hal_api_docs_with_contributors_version_1
    :param hal_api_docs_with_contributors_version_2
    :return:
    """
    # First request, will fetch the first version of the bibliographic records
    with mock.patch.object(aiohttp.ClientSession, "get") as aiohttp_client_session_get:
        aiohttp_client_session_get.return_value.__aenter__.return_value.status = 200
        aiohttp_client_session_get.return_value.__aenter__.return_value.json.return_value = (
            hal_api_docs_with_contributors_version_1
        )

        response = test_client.post(
            REFERENCES_RETRIEVAL_API_PATH,
            json={
                "person": person_with_name_and_id_hal_i_json,
                "events": ["created", "updated", "deleted", "unchanged"],
            },
        )
        assert response.status_code == 200
        json_response = response.json()
        retrieval_url = json_response["retrieval_url"]
        assert retrieval_url is not None
        response = test_client.get(retrieval_url)
        assert response.status_code == 200
        json_response = response.json()
        assert json_response["harvestings"][0]["state"] == "completed"
        assert json_response["harvestings"][0]["harvester"] == "hal"
        assert len(json_response["harvestings"][0]["reference_events"]) == 7
        events = json_response["harvestings"][0]["reference_events"]
        reference_1_v1_id = _extract_reference_id_by_source_identifier(
            events, "1-will-gain-second-contributor"
        )
        reference_1_v1_url = f"{REFERENCE_EVENTS_API_PATH}/{reference_1_v1_id}"
        response = test_client.get(reference_1_v1_url)
        assert response.status_code == 200
        reference_1_v1 = response.json()
        assert reference_1_v1 is not None
        reference_1_v1_contributions = reference_1_v1["reference"]["contributions"]
        assert len(reference_1_v1_contributions) == 1
        assert reference_1_v1_contributions[0]["rank"] == 0
        assert (
            _extract_contribution_by_rank(reference_1_v1_contributions, 0)[
                "contributor"
            ]["source_identifier"]
            == "169647"
        )
        assert (
            _extract_contribution_by_rank(reference_1_v1_contributions, 0)[
                "contributor"
            ]["name"]
            == "Alessandro Buccheri"
        )
        reference_2_v1_id = _extract_reference_id_by_source_identifier(
            events, "2-will-loose-a-contributor"
        )
        reference_2_v1_url = f"{REFERENCE_EVENTS_API_PATH}/{reference_2_v1_id}"
        response = test_client.get(reference_2_v1_url)
        assert response.status_code == 200
        reference_2_v1 = response.json()
        assert reference_2_v1 is not None
        reference_2_v1_contributions = reference_2_v1["reference"]["contributions"]
        assert len(reference_2_v1_contributions) == 2
        assert (
            _extract_contribution_by_rank(reference_2_v1_contributions, 0)[
                "contributor"
            ]["source_identifier"]
            == "169647"
        )
        assert (
            _extract_contribution_by_rank(reference_2_v1_contributions, 0)[
                "contributor"
            ]["name"]
            == "Alessandro Buccheri"
        )
        assert (
            _extract_contribution_by_rank(reference_2_v1_contributions, 1)[
                "contributor"
            ]["source_identifier"]
            == "222222"
        )
        assert (
            _extract_contribution_by_rank(reference_2_v1_contributions, 1)[
                "contributor"
            ]["name"]
            == "Alex Terieur"
        )
        reference_3_v1_id = _extract_reference_id_by_source_identifier(
            events, "3-will-have-a-contributor-keeping-his-id-but-changing-his-name"
        )
        reference_3_v1_url = f"{REFERENCE_EVENTS_API_PATH}/{reference_3_v1_id}"
        response = test_client.get(reference_3_v1_url)
        assert response.status_code == 200
        reference_3_v1 = response.json()
        reference_3_v1_contributions = reference_3_v1["reference"]["contributions"]
        reference_4_v1_id = _extract_reference_id_by_source_identifier(
            events, "4-will-have-a-contributor-keeping-his-name-but-changing-his-id"
        )
        reference_4_v1_url = f"{REFERENCE_EVENTS_API_PATH}/{reference_4_v1_id}"
        response = test_client.get(reference_4_v1_url)
        assert response.status_code == 200
        reference_4_v1 = response.json()
        reference_4_v1_contributions = reference_4_v1["reference"]["contributions"]
        reference_5_v1_id = _extract_reference_id_by_source_identifier(
            events, "5-has-a-contributor-with-name-only-will-change-his-name"
        )
        reference_5_v1_url = f"{REFERENCE_EVENTS_API_PATH}/{reference_5_v1_id}"
        response = test_client.get(reference_5_v1_url)
        assert response.status_code == 200
        reference_5_v1 = response.json()
        reference_5_v1_contributions = reference_5_v1["reference"]["contributions"]
        reference_6_v1_id = _extract_reference_id_by_source_identifier(
            events, "6-has-the-same-contributor-with-two-different-roles"
        )
        reference_6_v1_url = f"{REFERENCE_EVENTS_API_PATH}/{reference_6_v1_id}"
        response = test_client.get(reference_6_v1_url)
        assert response.status_code == 200
        reference_6_v1 = response.json()
        # assert that the contributor is present twice in the contributions list
        reference_6_v1_contributions = reference_6_v1["reference"]["contributions"]
        assert len(reference_6_v1_contributions) == 2
        # assert that the contributor is present twice in the contributions list
        for i in range(2):
            assert (
                _extract_contribution_by_rank(reference_6_v1_contributions, i)[
                    "contributor"
                ]["name"]
                == "Arnaud Dupont"
            )
        assert (
            _extract_contribution_by_rank(reference_6_v1_contributions, 0)["role"]
            != _extract_contribution_by_rank(reference_6_v1_contributions, 1)["role"]
        )
    # second request, will fetch the second version of the bibliographic records
    with mock.patch.object(aiohttp.ClientSession, "get") as aiohttp_client_session_get:
        aiohttp_client_session_get.return_value.__aenter__.return_value.status = 200
        aiohttp_client_session_get.return_value.__aenter__.return_value.json.return_value = (
            hal_api_docs_with_contributors_version_2
        )

        response = test_client.post(
            REFERENCES_RETRIEVAL_API_PATH,
            json={
                "person": person_with_name_and_id_hal_i_json,
                "events": ["created", "updated", "deleted", "unchanged"],
            },
        )
        assert response.status_code == 200
        json_response = response.json()
        retrieval_url = json_response["retrieval_url"]
        assert retrieval_url is not None
        response = test_client.get(retrieval_url)
        assert response.status_code == 200
        json_response = response.json()
        assert json_response["harvestings"][0]["state"] == "completed"
        events = json_response["harvestings"][0]["reference_events"]
        assert len(events) == 7
        reference_1_v2_id = _extract_reference_id_by_source_identifier(
            events, "1-will-gain-second-contributor"
        )
        reference_1_v2_url = f"{REFERENCE_EVENTS_API_PATH}/{reference_1_v2_id}"
        response = test_client.get(reference_1_v2_url)
        assert response.status_code == 200
        reference_1_v2 = response.json()
        assert reference_1_v2 is not None
        reference_1_v2_contributions = reference_1_v2["reference"]["contributions"]
        assert len(reference_1_v2_contributions) == 2
        # assert that the first contributor is the same as in reference_1_v1
        # and that there is a new one called 'Françoise Bas-Theron'
        assert (
            _extract_contribution_by_rank(reference_1_v2_contributions, 0)[
                "contributor"
            ]["name"]
            == _extract_contribution_by_rank(reference_1_v1_contributions, 0)[
                "contributor"
            ]["name"]
        )
        assert (
            _extract_contribution_by_rank(reference_1_v2_contributions, 0)[
                "contributor"
            ]["source_identifier"]
            == _extract_contribution_by_rank(reference_1_v1_contributions, 0)[
                "contributor"
            ]["source_identifier"]
        )
        assert (
            _extract_contribution_by_rank(reference_1_v2_contributions, 1)[
                "contributor"
            ]["name"]
            == "Françoise Bas-Theron"
        )
        reference_2_v2_id = _extract_reference_id_by_source_identifier(
            events, "2-will-loose-a-contributor"
        )
        reference_2_v2_url = f"{REFERENCE_EVENTS_API_PATH}/{reference_2_v2_id}"
        response = test_client.get(reference_2_v2_url)
        assert response.status_code == 200
        reference_2_v2 = response.json()
        reference_2_v2_contributions = reference_2_v2["reference"]["contributions"]
        assert reference_2_v2 is not None
        assert len(reference_2_v2_contributions) == 1
        # assert that the contributor is the same as the first one in reference_2_v1
        assert (
            _extract_contribution_by_rank(reference_2_v2_contributions, 0)[
                "contributor"
            ]["name"]
            == _extract_contribution_by_rank(reference_2_v1_contributions, 0)[
                "contributor"
            ]["name"]
        )
        assert (
            _extract_contribution_by_rank(reference_2_v2_contributions, 0)[
                "contributor"
            ]["source_identifier"]
            == _extract_contribution_by_rank(reference_2_v1_contributions, 0)[
                "contributor"
            ]["source_identifier"]
        )

        reference_3_v2_id = _extract_reference_id_by_source_identifier(
            events, "3-will-have-a-contributor-keeping-his-id-but-changing-his-name"
        )
        reference_3_v2_url = f"{REFERENCE_EVENTS_API_PATH}/{reference_3_v2_id}"
        response = test_client.get(reference_3_v2_url)
        assert response.status_code == 200
        reference_3_v2 = response.json()
        reference_3_v2_contributions = reference_3_v2["reference"]["contributions"]
        # the second contributor has the same id as in reference_3_v1 but a different name
        assert reference_3_v2 is not None
        assert len(reference_3_v2_contributions) == 2
        assert (
            _extract_contribution_by_rank(reference_3_v2_contributions, 1)[
                "contributor"
            ]["name"]
            == "Alain Terieur"
        )
        assert (
            _extract_contribution_by_rank(reference_3_v2_contributions, 1)[
                "contributor"
            ]["source_identifier"]
            == _extract_contribution_by_rank(reference_3_v1_contributions, 1)[
                "contributor"
            ]["source_identifier"]
        )
        # the name of the second contributor in the previous version
        # has been kept in the variant field
        assert (
            _extract_contribution_by_rank(reference_3_v1_contributions, 1)[
                "contributor"
            ]["name"]
            in _extract_contribution_by_rank(reference_3_v2_contributions, 1)[
                "contributor"
            ]["name_variants"]
        )
        reference_4_v2_id = _extract_reference_id_by_source_identifier(
            events, "4-will-have-a-contributor-keeping-his-name-but-changing-his-id"
        )
        reference_4_v2_url = f"{REFERENCE_EVENTS_API_PATH}/{reference_4_v2_id}"
        response = test_client.get(reference_4_v2_url)
        assert response.status_code == 200
        reference_4_v2 = response.json()
        reference_4_v2_contributions = reference_4_v2["reference"]["contributions"]
        # the second contributor has the same name as in reference_4_v1 but a different id
        assert reference_4_v2 is not None
        assert len(reference_4_v2_contributions) == 2
        assert (
            _extract_contribution_by_rank(reference_4_v2_contributions, 1)[
                "contributor"
            ]["name"]
            == _extract_contribution_by_rank(reference_4_v1_contributions, 1)[
                "contributor"
            ]["name"]
        )
        assert (
            _extract_contribution_by_rank(reference_4_v1_contributions, 1)[
                "contributor"
            ]["source_identifier"]
            == "222222"
        )
        assert (
            _extract_contribution_by_rank(reference_4_v2_contributions, 1)[
                "contributor"
            ]["source_identifier"]
            == "333333"
        )
        reference_5_v2_id = _extract_reference_id_by_source_identifier(
            events, "5-has-a-contributor-with-name-only-will-change-his-name"
        )
        reference_5_v2_url = f"{REFERENCE_EVENTS_API_PATH}/{reference_5_v2_id}"
        response = test_client.get(reference_5_v2_url)
        assert response.status_code == 200
        reference_5_v2 = response.json()
        reference_5_v2_contributions = reference_5_v2["reference"]["contributions"]
        # the only contributor had a name and no id in v1
        # he's got a new name but still no id in v2
        assert reference_5_v2 is not None
        assert len(reference_5_v2_contributions) == 1
        assert (
            _extract_contribution_by_rank(reference_5_v1_contributions, 0)[
                "contributor"
            ]["name"]
            == "Arnaud Dupont"
        )
        assert (
            _extract_contribution_by_rank(reference_5_v2_contributions, 0)[
                "contributor"
            ]["name"]
            == "Arnaud Durand"
        )
        assert (
            _extract_contribution_by_rank(reference_5_v1_contributions, 0)[
                "contributor"
            ]["source_identifier"]
            is None
        )
        assert (
            _extract_contribution_by_rank(reference_5_v2_contributions, 0)[
                "contributor"
            ]["source_identifier"]
            == "153764"
        )


def _extract_reference_id_by_source_identifier(events, source_identifier):
    for event in events:
        if event["reference"]["source_identifier"] == source_identifier:
            return event.get("id")
    return None


def _extract_contribution_by_rank(contributions, rank):
    return next(c for c in contributions if c["rank"] == rank)
