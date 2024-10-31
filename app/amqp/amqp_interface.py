import asyncio
from asyncio import sleep

import aio_pika
from aio_pika import ExchangeType
from loguru import logger
from starlette.datastructures import State

from app.amqp.amqp_message_processor import AMQPMessageProcessor
from app.settings.app_settings import AppSettings

DEFAULT_RESULT_TIMEOUT = 600


# pylint: disable=too-many-instance-attributes
class AMQPInterface:
    """Rabbitmq Connexion abstraction"""

    def __init__(self, settings: AppSettings, state: State):
        """
        Init AMQP Connexion class

        :param settings: AppSettings
        :param state: fastapi app state

        """
        self.settings = settings
        self.app_state = state
        self.app_state.amqp_disconnected = False
        self.pika_queue: aio_pika.Queue | None = None
        self.pika_channel: aio_pika.Channel | None = None
        self.pika_exchange: aio_pika.Exchange | None = None
        self.pika_connexion: aio_pika.abc.AbstractRobustConnection | None = None
        self.inner_tasks_queue: asyncio.Queue | None = None
        self.message_processing_workers: list[asyncio.Task] | None = None
        self.keys = [self.settings.amqp_retrieval_routing_key]
        self.reconnect_event = asyncio.Event()

    async def connect(self):
        """Connect to AMQP queue"""
        await self._connect()
        await self._declare_exchange()
        await self._attach_message_processing_workers()
        await self._bind_queue()
        asyncio.create_task(self._listen_for_reconnect())
        await sleep(0)

    async def _listen_for_reconnect(self):
        """Listen for reconnect signals from worker tasks."""
        await self.reconnect_event.wait()  # Wait until reconnect is triggered
        logger.error("Reconnect signal received. Positioning flag in app state.")
        self.app_state.amqp_disconnected = True

    async def listen(self):
        """Listen to AMQP queue"""
        await self._listen_to_messages()

    async def stop_listening(self) -> None:
        """Stop listening to AMQP queue"""
        try:
            await asyncio.wait_for(
                self.inner_tasks_queue.join(),
                timeout=self.settings.amqp_wait_before_shutdown,
            )
        finally:
            for worker in self.message_processing_workers:
                worker.cancel()
            await self.pika_channel.close()
            await self.pika_connexion.close()

    async def _attach_message_processing_workers(self):
        self.message_processing_workers = []
        self.inner_tasks_queue = asyncio.Queue(maxsize=self.settings.inner_task_queue_length)
        for worker_id in range(self.settings.inner_task_parallelism_limit):
            processor = await self._message_processor()
            self.message_processing_workers.append(
                asyncio.create_task(
                    processor.wait_for_message(worker_id),
                    name=f"amqp_message_processor_{worker_id}",
                )
            )

    async def _message_processor(self):
        return AMQPMessageProcessor(
            exchange=self.pika_exchange,
            tasks_queue=self.inner_tasks_queue,
            settings=self.settings,
            reconnect_event=self.reconnect_event,
        )

    async def _listen_to_messages(self):
        while True:
            if self.inner_tasks_queue.full():
                logger.debug(
                    f"Queue is full with {self.inner_tasks_queue.qsize()} messages, "
                    f"pausing message consumption."
                )
                await asyncio.sleep(0.1)
                continue
            if self.app_state.amqp_disconnected:
                logger.warning("AMQP disconnected. Pausing message consumption.")
                await asyncio.sleep(0.1)
                continue
            message = await self.pika_queue.get(no_ack=True, fail=False)
            if message is None:
                await asyncio.sleep(0.5)
                logger.warning("No message received, go on listening")
                continue
            message_id = message.message_id
            logger.info(f"Accepted new message : {message_id}")
            await self.inner_tasks_queue.put(message)
            logger.debug(f"Current size of inner tasks queue after adding message:"
                         f" {self.inner_tasks_queue.qsize()}")

    async def _declare_exchange(self) -> None:
        """
        Declare the publication exchange
        :return: None
        """
        self.pika_exchange = await self.pika_channel.declare_exchange(
            self.settings.amqp_exchange_name, ExchangeType.TOPIC, durable=True
        )

    async def _bind_queue(self) -> None:
        # Bind service message queue to publication exchange
        await self.pika_channel.set_qos(
            prefetch_count=self.settings.amqp_prefetch_count
        )
        self.pika_queue = await self.pika_channel.declare_queue(
            self.settings.amqp_queue_name,
            durable=True,
            arguments={"x-consumer-timeout": self.settings.amqp_consumer_ack_timeout},
        )
        for key in self.keys:
            await self.pika_queue.bind(self.pika_exchange, routing_key=key)

    async def _connect(self) -> None:
        self.pika_connexion: aio_pika.Connection = await aio_pika.connect_robust(
            f"amqp://{self.settings.amqp_user}:"
            f"{self.settings.amqp_password}"
            f"@{self.settings.amqp_host}/",
        )
        self.pika_channel = await self.pika_connexion.channel(publisher_confirms=True)
