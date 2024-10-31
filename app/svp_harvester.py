import asyncio
import sys

from aiormq import AMQPConnectionError
from fastapi import FastAPI
from loguru import logger
from pydantic import ValidationError
from sqlalchemy import text
from starlette.staticfiles import StaticFiles

from app.amqp.amqp_interface import AMQPInterface
from app.api.errors.validation_error import http422_error_handler
from app.api.routes.api import router as api_router
from app.api.routes.healthness import router as healthness_router
from app.config import get_app_settings
from app.db.session import async_session
from app.gui.routes.gui import router as gui_router
from app.redis.redis_pool import RedisPool
from app.settings.app_env_types import AppEnvTypes


class SvpHarvester(FastAPI):
    """Main application, routing logic, middlewares and startup/shutdown events"""

    # All middlewares have been disabled due to Faspi/Starlette bug
    # https://stackoverflow.com/questions/70043665/fastapi-unvicorn-request-hanging-during-invocation-of-call-next-path-operation
    # https://stackoverflow.com/questions/68830274/blocked-code-while-using-middleware-and-dependency-injections-to-log-requests-in

    def __init__(self):
        super().__init__()
        # only if app_env == "dev"
        if get_app_settings().app_env == AppEnvTypes.DEV:
            import asyncio
            asyncio.get_event_loop().set_debug(True)
        self.amqp_interface: AMQPInterface | None = None

        settings = get_app_settings()

        self.include_router(
            api_router, prefix=f"{settings.api_prefix}/{settings.api_version}"
        )

        self.include_router(healthness_router, prefix="/health")

        self.mount(
            "/static", StaticFiles(directory="./app/static", html=True), name="static"
        )

        self.include_router(gui_router)

        if settings.svp_jel_proxy_url is not None:
            logger.info(
                f"JEL Sparql endpoint has been set to {settings.svp_jel_proxy_url}"
            )
        else:
            logger.warning(
                "JEL Sparql endpoint has not been set, "
                "JEL concepts URIs wille be resolved against ZBW Skosmos instance"
            )

        # Remove default logger and add custom logger
        logger.remove()
        logger.add(
            settings.logger_sink,
            level=settings.loguru_level,
            **({"rotation": "100 MB"} if settings.logger_sink != sys.stderr else {}),
        )
        self.add_exception_handler(ValidationError, http422_error_handler)
        self.add_event_handler("startup", self.check_db_connexion)
        if settings.third_api_caching_enabled:
            self.add_event_handler("startup", self.check_redis_connexion)
        if settings.amqp_enabled:
            self.add_event_handler("startup", self.open_rabbitmq_connexion)
            self.add_event_handler("shutdown", self.close_rabbitmq_connexion)

    @logger.catch(reraise=True)
    async def check_db_connexion(self) -> None:
        """
        Check database connexion at boot time
        to help ensure container startup order
        :return: None
        """
        logger.info("Checking database connexion readiness")
        async with async_session() as session:
            try:
                await session.execute(text("SELECT 1"))
                logger.info("Database connexion is ready")
            except ConnectionRefusedError as error:
                logger.error(
                    "Cannot connect to database : ConnectionRefusedError, "
                    f"will retry in 1 second : {error}"
                )
                await asyncio.sleep(1)
                await self.check_db_connexion()
            except Exception as error:
                logger.error(
                    "Cannot connect to database : Unknown error, will not retry"
                )
                raise error

    @logger.catch(reraise=True)
    async def check_redis_connexion(self) -> None:
        """
        Check Redis connexion at boot time
        to help ensure container startup order
        :return: None
        """
        logger.info("Checking Redis connexion readiness")
        try:
            if await RedisPool().check_ready():
                logger.info("Redis connexion is ready")
            else:
                logger.error("Cannot connect to redis, will retry in 1 second")
                await asyncio.sleep(1)
                await self.check_redis_connexion()
        except Exception as error:
            logger.error("Cannot connect to Redis : Unknown error, will not retry")
            raise error

    @logger.catch(reraise=True)
    async def open_rabbitmq_connexion(self) -> None:  # pragma: no cover
        """Init AMQP connexion at boot time"""
        try:
            logger.info("Enabling RabbitMQ connexion")
            self.amqp_interface = AMQPInterface(get_app_settings(), self.state)
            await self.amqp_interface.connect()
            asyncio.create_task(self.amqp_interface.listen(), name="amqp_listener")
            logger.info("RabbitMQ connexion has been enabled")
        except AMQPConnectionError as error:
            logger.error(
                f"Cannot connect to RabbitMQ : AMQPConnectionError, will retry in 1 second : "
                f"{error}"
            )
            await asyncio.sleep(1)
            await self.open_rabbitmq_connexion()
        except Exception as error:
            logger.error("Cannot connect to RabbitMQ : Unknown error, will not retry")
            raise error

    async def close_rabbitmq_connexion(self) -> None:  # pragma: no cover
        """Handle last tasks before shutdown"""
        logger.info("Closing RabbitMQ connexion")
        await self.amqp_interface.stop_listening()
        logger.info("RabbitMQ connexion has been closed")
