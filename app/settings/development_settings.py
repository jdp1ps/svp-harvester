"""
Settings for development environment
"""
import logging
import sys
from typing import ClassVar, TextIO

from pydantic_settings import SettingsConfigDict

from app.settings.app_settings import AppSettings


class DevAppSettings(AppSettings):
    """
    Settings for development environment
    """

    debug: bool = True

    logging_level: int = logging.DEBUG

    loguru_level: str = "DEBUG"

    logger_sink: ClassVar[str | TextIO] = sys.stderr

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    institution_name: str = "XYZ University • instance développement"

    monitor_loop_lag: bool = False

    loop_lag_threshold: float = 0.5
