import asyncio
import json
import traceback
from datetime import datetime

import aio_pika
from aio_pika import IncomingMessage
from aiormq import ChannelInvalidStateError, AMQPError
from asyncpg import PostgresConnectionError
from loguru import logger
from pydantic import ValidationError

from app.amqp.amqp_message_publisher import AMQPMessagePublisher
from app.db.models.retrieval import Retrieval
from app.harvesters.exceptions.invalid_entity_error import InvalidEntityError
from app.models.people import Person
from app.services.retrieval.retrieval_service import RetrievalService
from app.settings.app_settings import AppSettings

DEFAULT_RESULT_TIMEOUT = 600


class AMQPMessageProcessor:
    """
    Workers to process messages from AMQP interface
    """

    MAX_EXPECTED_RESULTS = 10000

    def __init__(
        self,
        exchange: aio_pika.Exchange,
        tasks_queue: asyncio.Queue,
        settings: AppSettings,
        reconnect_event: asyncio.Event,
    ):
        self.exchange = exchange
        self.tasks_queue = tasks_queue
        self.settings = settings
        self.reconnect_event = reconnect_event
        self._init_publisher()

    def _init_publisher(self) -> None:
        self.publisher = AMQPMessagePublisher(self.exchange)

    async def wait_for_message(self, worker_id: int) -> None:
        """
        Messages awaiting method for async processing
        :param worker_id: queue worker identifier
        :return: None
        """
        message: IncomingMessage | None = None

        while True:
            requeue = False
            start_time = datetime.now()
            try:
                message = await self.tasks_queue.get()
                start_time = datetime.now()
                payload = await self._get_message_payload(
                    message, start_time, worker_id
                )
                await self._process_message(payload)
                self.tasks_queue.task_done()
                logger.debug(
                    f"Message {message.message_id}  processed by {worker_id} in "
                    f"{datetime.now() - start_time}"
                )
            except ChannelInvalidStateError as channel_error:
                await self._handle_channel_failure(channel_error, worker_id)
                return
            except AMQPError as ack_error:
                requeue = await self._handle_amqp_error(ack_error, worker_id)
            except KeyboardInterrupt as keyboard_interrupt:
                await self._handle_application_stop(
                    keyboard_interrupt, message, worker_id
                )
            except InvalidEntityError as invalid_entity_error:
                requeue = await self._handle_invalid_entity(invalid_entity_error)
            except (ConnectionError, PostgresConnectionError) as connection_error:
                requeue = await self._handle_database_error(connection_error, worker_id)
            except Exception as exception:  # pylint: disable=broad-exception-caught
                requeue = await self._handle_unexpected_error(exception, worker_id)
            finally:
                await self._post_process_message(message, requeue, worker_id)
                end_time = datetime.now()
                logger.warning(
                    f"Performance : Message  processed by {worker_id} "
                    f"in {end_time - start_time} for payload {payload}"
                )

    async def _post_process_message(self, message, requeue, worker_id):
        if message is not None and not message.processed:
            try:
                await message.nack(requeue=requeue)
            except ChannelInvalidStateError as channel_error:
                logger.error(
                    f"Error during message nack for {worker_id} : {channel_error}"
                )
                self.reconnect_event.set()
            except AMQPError as nack_error:
                logger.error(
                    f"AMQP error during message nack for {worker_id} : {nack_error}"
                )
                self.reconnect_event.set()
            self.tasks_queue.task_done()

    async def _handle_unexpected_error(self, exception, worker_id):
        logger.error(
            f"Unexpected exception during {worker_id} message processing: {exception}"
        )
        logger.error(traceback.format_exc())
        return True

    async def _handle_database_error(self, connection_error, worker_id):
        logger.error(
            f"Connection refused during {worker_id} message processing : {connection_error}"
        )
        return True

    @staticmethod
    async def _handle_invalid_entity(invalid_entity_error):
        logger.error(f"Invalid entity submitted : {invalid_entity_error}")
        return False

    @staticmethod
    async def _handle_application_stop(keyboard_interrupt, message, worker_id):
        logger.warning(f"Amqp connect worker {worker_id} has been cancelled")
        if message is not None and not message.processed:
            await message.nack(requeue=True)
        raise keyboard_interrupt

    async def _handle_amqp_error(self, ack_error, worker_id):
        logger.error(f"AMQP error occurred during {worker_id} message ack: {ack_error}")
        self.reconnect_event.set()
        return True

    async def _handle_channel_failure(self, channel_error, worker_id):
        logger.error(
            f"Channel invalid state error during {worker_id} "
            f"message ack: {channel_error}"
        )
        self.reconnect_event.set()

    @staticmethod
    async def _get_message_payload(message, start_time, worker_id):
        payload: bytes = None
        async with message.process(ignore_processed=True):
            payload = message.body
            ack_time = datetime.now()
            logger.debug(
                f"Message {message.message_id}  acked by {worker_id} in {ack_time - start_time}"
            )
        return payload

    async def _process_message(self, payload: str, timeout=DEFAULT_RESULT_TIMEOUT):
        json_payload = json.loads(payload)
        reply_expected = json_payload.get("reply", False)

        if json_payload["type"] == "person":
            try:
                person = Person(**json_payload["fields"])
            except ValidationError as validation_error:
                await self.publisher.publish(
                    {
                        "type": "Retrieval",
                        "error": True,
                        "message": f"Entity validation error,"
                        f" retrieval aborted: {validation_error}",
                        "parameters": json_payload,
                    }
                )
                raise InvalidEntityError(
                    f"Entity validation error: {validation_error} in {json_payload}"
                ) from validation_error

            if person.has_no_bibliographic_identifiers():
                await self.publisher.publish(
                    {
                        "type": "Retrieval",
                        "error": True,
                        "message": "No identifiers provided, retrieval aborted",
                        "parameters": json_payload,
                    }
                )
                raise InvalidEntityError("No identifiers provided in {json_payload}")
            service = RetrievalService(
                identifiers_safe_mode=json_payload.get("identifiers_safe_mode", False),
                nullify=json_payload.get("nullify", False),
                harvesters=json_payload.get("harvesters", []),
                events=json_payload.get("events", []),
            )
            # Create a queue to get results back
            if reply_expected:
                retrieval_results_queue = asyncio.Queue(
                    maxsize=self.MAX_EXPECTED_RESULTS
                )
            # Resister a new retrieval in DB
            retrieval = await service.register(entity=person)
            if reply_expected:
                await self.publisher.publish(
                    {
                        "type": "Retrieval",
                        "id": retrieval.id,
                    }
                )
            # Run the retrieval
            run_task_name = f"amqp_retrieval_service_{retrieval.id}_launcher"
            # Listen for results
            if reply_expected:
                listen = asyncio.create_task(
                    self._wait_for_retrieval_result(
                        result_queue=retrieval_results_queue,
                        retrieval=retrieval,
                        timeout=timeout,
                    ),
                    name=f"amqp_retrieval_service_{retrieval.id}_listener",
                )

            if reply_expected:
                tasks = [
                    asyncio.create_task(
                        service.run(result_queue=retrieval_results_queue),
                        name=run_task_name,
                    ),
                    listen,
                ]
                await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            else:
                await service.run()
            if reply_expected:
                listen.cancel()

    async def _wait_for_retrieval_result(
        self, result_queue: asyncio.Queue, retrieval: Retrieval, timeout: int
    ):
        try:
            while True:
                result = await asyncio.wait_for(result_queue.get(), timeout=timeout)
                logger.debug(f"Got result {result} for retrieval: {retrieval.id}")
                asyncio.create_task(self.publisher.publish(result))
                await asyncio.sleep(0)
        except asyncio.TimeoutError:
            message = f"Retrieval {retrieval.id} results timeout"
            logger.warning(message)
            await self.publisher.publish(
                {
                    "type": "Retrieval",
                    "error": True,
                    "message": message,
                    "id": retrieval.id,
                }
            )
        except KeyboardInterrupt:
            message = f"Retrieval {retrieval.id} results processing has been cancelled"
            logger.warning(message)
            await self.publisher.publish(
                {
                    "type": "Retrieval",
                    "error": True,
                    "message": message,
                    "id": retrieval.id,
                }
            )
        except Exception as exception:
            message = f"Exception during retrieval {retrieval.id} results processing: {exception}"
            logger.error(message)
            await self.publisher.publish(
                {
                    "type": "Retrieval",
                    "error": True,
                    "message": message,
                    "id": retrieval.id,
                }
            )
            raise exception
