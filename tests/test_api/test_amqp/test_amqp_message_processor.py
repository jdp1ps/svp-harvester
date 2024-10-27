"""Test the references API."""

from unittest import mock

import pytest

from app.amqp.amqp_interface import AMQPInterface
from app.amqp.amqp_message_processor import AMQPMessageProcessor
from app.amqp.amqp_message_publisher import AMQPMessagePublisher
from app.config import get_app_settings
from app.models.people import Person
from app.services.retrieval.retrieval_service import RetrievalService


@pytest.fixture(name="mock_retrieval_service_init")
def fixture_mock_retrieval_service_init():
    """Retrieval service mock to detect constructor method calls."""
    with mock.patch.object(RetrievalService, "__init__", autospec=True) as service:
        service.return_value = None
        yield service


@pytest.fixture(name="mock_retrieval_service_register")
def fixture_mock_retrieval_service_register():
    """Retrieval service mock to detect mock_retrieval_service_register method calls."""
    with mock.patch.object(RetrievalService, "register", autospec=True) as service:
        yield service


@pytest.fixture(name="mock_retrieval_service_run")
def fixture_mock_retrieval_service_run():
    """Retrieval service mock to detect run method calls."""
    with mock.patch.object(RetrievalService, "run", autospec=True) as service:
        yield service


@pytest.fixture(name="message_processor")
async def fixture_message_processor(test_app) -> AMQPMessageProcessor:
    """AMQP message processor fixture to use AMQPInterface as factory."""
    amqp_connexion = AMQPInterface(get_app_settings(), state=test_app.state)
    # pylint: disable=protected-access
    return await amqp_connexion._message_processor()


async def test_amqp_message_runs_retrieval_service(
    message_processor: AMQPMessageProcessor,
    mock_retrieval_service_init,
    mock_retrieval_service_register,
    mock_retrieval_service_run,
):
    """Test that the retrieval service is called when a message is received."""
    payload = (
        '{"type": "person", '
        '"fields": {'
        '"name": "Doe, John", '
        '"identifiers": [{"type": "orcid", "value": "0000-0002-1825-0097"}]'
        "}}"
    )
    with mock.patch.object(AMQPMessagePublisher, "publish", autospec=True):
        # pylint: disable=protected-access
        await message_processor._process_message(payload, 1)
        mock_retrieval_service_init.assert_called_once()
        mock_retrieval_service_register.assert_called_once()
        _, init_args = mock_retrieval_service_init.call_args
        _, register_args = mock_retrieval_service_register.call_args
        assert init_args["identifiers_safe_mode"] is False
        assert init_args["nullify"] is False
        assert init_args["events"] == []
        # register args is a dict and it as pydantic person under 'entity' key
        assert isinstance(register_args["entity"], Person)
        assert register_args["entity"].name == "Doe, John"
        assert register_args["entity"].identifiers[0].type == "orcid"
        assert register_args["entity"].identifiers[0].value == "0000-0002-1825-0097"
        mock_retrieval_service_run.assert_called_once()


@pytest.mark.asyncio
async def test_amqp_message_runs_retrieval_service_with_parameters(
    message_processor: AMQPMessageProcessor,
    mock_retrieval_service_init,
    mock_retrieval_service_register,
    mock_retrieval_service_run,  # pylint: disable=unused-argument
):
    """Test that the retrieval service is called when a message is received."""
    payload = (
        '{"type": "person", '
        '"fields": {"name": "Doe, John", '
        '"identifiers": [{"type": "orcid", "value": "0000-0002-1825-0097"}]},'
        '"identifiers_safe_mode": true, '
        '"reply": true, '
        '"nullify": ["orcid"], '
        '"events": ["updated"]}'
    )
    with mock.patch.object(AMQPMessagePublisher, "publish", autospec=True):
        # pylint: disable=protected-access
        await message_processor._process_message(payload, 1)
        mock_retrieval_service_init.assert_called_once()
        mock_retrieval_service_register.assert_called_once()
        _, init_args = mock_retrieval_service_init.call_args
        assert init_args["identifiers_safe_mode"] is True
        assert init_args["nullify"] == ["orcid"]
        assert init_args["events"] == ["updated"]
