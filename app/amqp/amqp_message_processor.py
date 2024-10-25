import asyncio
import json
from datetime import datetime

import aio_pika
from aio_pika import IncomingMessage
from asyncpg import PostgresConnectionError
from loguru import logger
from pydantic import ValidationError

from app.amqp.amqp_message_publisher import AMQPMessagePublisher
from app.db.models.retrieval import Retrieval
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
    ):
        self.exchange = exchange
        self.tasks_queue = tasks_queue
        self.settings = settings
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
        try:
            while True:
                message = await self.tasks_queue.get()
                start_time = datetime.now()
                async with message.process(ignore_processed=True):
                    payload = message.body
                    await self._process_message(payload)
                    await message.ack()
                    self.tasks_queue.task_done()
                    end_time = datetime.now()
                    logger.warning(
                        f"Performance : Message  processed by {worker_id} "
                        f"in {end_time - start_time} for payload {payload}"
                    )
        except KeyboardInterrupt:
            await message.nack(requeue=True)
            logger.warning(f"Amqp connect worker {worker_id} has been cancelled")
        except (ConnectionError, PostgresConnectionError) as connection_error:
            await message.nack(requeue=True)
            logger.error(
                f"Connection refused during {worker_id} message processing : {connection_error}"
            )
        except Exception as exception:
            await message.nack(requeue=True)
            logger.error(
                f"Unexpected exception during {worker_id} message processing : {exception}"
            )
            raise exception

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
                return
            if person.has_no_bibliographic_identifiers():
                await self.publisher.publish(
                    {
                        "type": "Retrieval",
                        "error": True,
                        "message": "No identifiers provided, retrieval aborted",
                        "parameters": json_payload,
                    }
                )
                return
            service = RetrievalService(
                identifiers_safe_mode=json_payload.get("identifiers_safe_mode"),
                nullify=json_payload.get("nullify"),
                harvesters=json_payload.get("harvesters"),
                events=json_payload.get("events"),
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
