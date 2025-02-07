"""Test AMQP publishing capabilities."""

import json
from unittest.mock import Mock

import pytest
from aio_pika import Exchange, DeliveryMode
from sqlalchemy.ext.asyncio import AsyncSession

from app.amqp.amqp_message_publisher import AMQPMessagePublisher


@pytest.mark.asyncio
async def test_publish_harvesting_status(
    async_session: AsyncSession,
    mocked_message: Mock,
    mocked_exchange: Exchange,
    harvesting_db_model_for_person_with_idref,
):
    """Test that a message is published to the AMQP queue when the publish method is called."""
    async_session.add(harvesting_db_model_for_person_with_idref)
    await async_session.commit()

    amqp_message_publisher = AMQPMessagePublisher(mocked_exchange)
    received_message_payload = {
        "type": "Harvesting",
        "id": harvesting_db_model_for_person_with_idref.id,
    }
    expected_sent_message_payload = {
        "harvester": "idref",
        "state": "running",
        "error": [],
        "entity": {
            "identifiers": [{"type": "idref", "value": "123456789"}],
            "name": "John Doe",
        },
    }
    expected_sent_message_routing_key = "event.references.harvesting.state"
    await amqp_message_publisher.publish(received_message_payload)
    mocked_message.assert_called_once_with(
        json.dumps(expected_sent_message_payload).encode(),
        delivery_mode=DeliveryMode.PERSISTENT,
    )
    mocked_exchange.publish.assert_called_once_with(
        message=mocked_message.return_value,
        routing_key=expected_sent_message_routing_key,
    )


@pytest.mark.asyncio
async def test_publish_created_reference(
    async_session: AsyncSession,
    mocked_message: Mock,
    mocked_exchange: Exchange,
    reference_event_db_model,
):
    """Test that a message is published to the AMQP queue when the publish method is called."""
    async_session.add(reference_event_db_model)
    await async_session.commit()

    amqp_message_publisher = AMQPMessagePublisher(mocked_exchange)
    received_message_payload = {
        "type": "ReferenceEvent",
        "id": reference_event_db_model.id,
        "state": "created",
    }
    expected_sent_message_payload = {
        "reference_event": {
            "type": "created",
            "reference": {
                "source_identifier": "123456789",
                "harvester": "hal",
                "harvester_version": "0.0.0",
                "identifiers": [],
                "manifestations": [],
                "titles": [{"value": "title", "language": "fr"}],
                "subtitles": [{"value": "subtitle", "language": "fr"}],
                "abstracts": [],
                "subjects": [
                    {
                        "uri": "http://uri",
                        "dereferenced": False,
                        "pref_labels": [{"value": "label", "language": "fr"}],
                        "alt_labels": [],
                    }
                ],
                "document_type": [],
                "contributions": [],
                "issue": None,
                "page": None,
                "book": None,
                "raw_issued": "2017",
                "issued": "2017-01-01 00:00:00",
                "created": "2018-02-02 10:00:00",
                "version": 0,
            },
            "enhanced": False,
        },
        "entity": {
            "identifiers": [{"type": "idref", "value": "123456789"}],
            "name": "John Doe",
        },
    }

    expected_sent_message_routing_key = "event.references.reference.created"
    await amqp_message_publisher.publish(received_message_payload)
    mocked_message.assert_called_once_with(
        json.dumps(expected_sent_message_payload).encode(),
        delivery_mode=DeliveryMode.PERSISTENT,
    )
    mocked_exchange.publish.assert_called_once_with(
        message=mocked_message.return_value,
        routing_key=expected_sent_message_routing_key,
    )


@pytest.mark.asyncio
async def test_publish_retrieval_error(
    async_session: AsyncSession,
    mocked_message: Mock,
    mocked_exchange: Exchange,
    harvesting_db_model_for_person_with_idref,
):
    """Test that a message is published to the AMQP queue when the publish method is called."""
    async_session.add(harvesting_db_model_for_person_with_idref)
    await async_session.commit()

    amqp_message_publisher = AMQPMessagePublisher(mocked_exchange)
    received_message_payload = {
        "type": "Retrieval",
        "error": True,
        "message": "Entity validation error, retrieval aborted",
        "parameters": {
            "type": "person",
            "identifiers_safe_mode": False,
            "fields": {
                "name": "C. Despas",
                "identifiers": [
                    {"type": "id_hal_s", "value": "christelle-despas"},
                    {"type": "id_hal_i", "value": "19550"},
                    {"type": "idref", "value": "158013263"},
                    {"type": "foo", "value": "bar"},
                ],
            },
        },
    }
    expected_sent_message_payload = {
        "type": "Retrieval",
        "parameters": received_message_payload["parameters"],
        "message": "Entity validation error, retrieval aborted",
    }
    expected_sent_message_routing_key = "event.references.retrieval.error"
    await amqp_message_publisher.publish(received_message_payload)
    mocked_message.assert_called_once_with(
        json.dumps(expected_sent_message_payload).encode(),
        delivery_mode=DeliveryMode.PERSISTENT,
    )
    mocked_exchange.publish.assert_called_once_with(
        message=mocked_message.return_value,
        routing_key=expected_sent_message_routing_key,
    )
