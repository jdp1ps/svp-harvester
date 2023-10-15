import pytest_asyncio

from app.db.daos.harvesting_dao import HarvestingDAO
from app.db.models.harvesting import Harvesting


@pytest_asyncio.fixture(name="harvesting_db_model")
async def fixture_harvesting_db_model(async_session, retrieval_db_model):
    """
    Generate a harvesting with a retrieval in DB model format

    :param async_session: async db session
    :param retrieval_db_model: retrieval in DB model format
    :return:  harvesting in DB model format
    """
    return await HarvestingDAO(async_session).create_harvesting(
        retrieval_db_model, "idref", Harvesting.State.RUNNING
    )


@pytest_asyncio.fixture(name="hal_harvesting_db_model_id_hal_i")
async def fixture_hal_harvesting_db_model_id_hal_i(
    async_session, retrieval_db_model_for_person_with_id_hal_i
):
    """
    Generate a Hal harvesting with a retrieval in DB model format for person with ID_HAL_I

    :param async_session: async db session
    :param retrieval_db_model_for_person_with_id_hal_i: retrieval in DB model format
    :return:  Hal harvesting in DB model format
    """
    return await HarvestingDAO(async_session).create_harvesting(
        retrieval_db_model_for_person_with_id_hal_i, "hal", Harvesting.State.RUNNING
    )


@pytest_asyncio.fixture(name="hal_harvesting_db_model_id_hal_s")
async def fixture_hal_harvesting_db_model_id_hal_s(
    async_session, retrieval_db_model_for_person_with_id_hal_s
):
    """
    Generate a Hal harvesting with a retrieval in DB model format for person with ID_HAL_I

    :param async_session: async db session
    :param retrieval_db_model_for_person_with_id_hal_s: retrieval in DB model format
    :return:  Hal harvesting in DB model format
    """
    return await HarvestingDAO(async_session).create_harvesting(
        retrieval_db_model_for_person_with_id_hal_s, "hal", Harvesting.State.RUNNING
    )


@pytest_asyncio.fixture(name="hal_harvesting_db_model_id_hal_i_s")
async def fixture_hal_harvesting_db_model_id_hal_i_s(
    async_session, retrieval_db_model_for_person_with_id_hal_i_s
):
    """
    Generate a Hal harvesting with a retrieval in DB model format for person with ID_HAL_I

    :param async_session: async db session
    :param retrieval_db_model_for_person_with_id_hal_i_s: retrieval in DB model format
    :return:  Hal harvesting in DB model format
    """
    return await HarvestingDAO(async_session).create_harvesting(
        retrieval_db_model_for_person_with_id_hal_i_s, "hal", Harvesting.State.RUNNING
    )
