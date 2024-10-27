import json

import aio_pika
from aio_pika import DeliveryMode
from aiormq import AMQPError, ChannelInvalidStateError
from loguru import logger

from app.amqp.amqp_harvesting_message_factory import AMQPHarvestingMessageFactory
from app.amqp.amqp_reference_event_message_factory import (
    AMQPReferenceEventMessageFactory,
)
from app.amqp.amqp_retrieval_message_factory import AMQPRetrievalMessageFactory

DEFAULT_RESULT_TIMEOUT = 600


class AMQPMessagePublisher:
    """Rabbitmq Publisher abstraction"""

    def __init__(self, exchange: aio_pika.Exchange):
        """Init AMQP Publisher class"""
        self.exchange = exchange

    async def publish(self, content: dict) -> None:
        """Publish a message to the AMQP queue."""
        payload, routing_key = await self._build_message(content)
        if routing_key is None:
            return

        message = aio_pika.Message(
            json.dumps(payload, default=str).encode(),
            delivery_mode=DeliveryMode.PERSISTENT,
        )
        try:
            await self.exchange.publish(
                message=message,
                routing_key=routing_key,
            )
            logger.debug(f"Message published to {routing_key} queue : {payload}")
        except AMQPError as e:
            logger.error(
                f"AMQP error occurred while publishing message to {routing_key} queue: {e}\n"
                f"Payload: {payload}"
            )
        except ChannelInvalidStateError as e:
            logger.error(
                f"Channel state error occurred while publishing message to "
                f"{routing_key} queue: {e}\nPayload: {payload}"
            )

    @staticmethod
    async def _build_message(content) -> tuple[str | None, str | None]:
        if content.get("type") == "Retrieval":
            return await AMQPRetrievalMessageFactory(content).build_message()
        if content.get("type") == "Harvesting":
            return await AMQPHarvestingMessageFactory(content).build_message()
        if content.get("type") == "ReferenceEvent":
            return await AMQPReferenceEventMessageFactory(content).build_message()
        return None, None
