import asyncio
import inspect
import time

from loguru import logger

from app.config import get_app_settings
from app.settings.app_env_types import AppEnvTypes


def execution_timer(function):
    """
    Decorator that can be used to measure execution time of function method
    :param function:
    :return:
    """
    def sync_wrapper(*args, **kwargs):
        if get_app_settings().app_env != AppEnvTypes.PROD:
            start = time.time()
            result = function(*args, **kwargs)
            duration = time.time() - start
            function_name = function.__name__
            function_path = inspect.getfile(function)
            logger.info(
                f"Execution time of {function_name} (defined in {function_path}): {duration} "
                f"seconds")
        else:
            result = function(*args, **kwargs)
        return result

    async def async_wrapper(*args, **kwargs):
        if get_app_settings().app_env != AppEnvTypes.PROD:
            start = time.time()
            result = await function(*args, **kwargs)
            duration = time.time() - start
            function_name = function.__name__
            function_path = inspect.getfile(function)
            logger.info(
                f"Execution time of {function_name} (defined in {function_path}): {duration} "
                f"seconds")
        else:
            result = await function(*args, **kwargs)
        return result

    if asyncio.iscoroutinefunction(function):
        return async_wrapper

    return sync_wrapper
