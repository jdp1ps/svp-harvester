"""
Settings for test environment
"""
import logging
import os

from pydantic_settings import SettingsConfigDict

from app.settings.app_settings import AppSettings


class TestAppSettings(AppSettings):
    """
    Settings for test environment
    """

    debug: bool = True

    logging_level: int = logging.DEBUG

    loguru_level: str = "DEBUG"

    model_config = SettingsConfigDict(env_file=".test.env", extra="ignore")

    harvesters_settings_file: str = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "..",
        "..",
        "tests",
        "harvesters-tests.yml",
    )

    harvesters: list[dict] = AppSettings.lst_from_yml(harvesters_settings_file)

    identifiers_settings_file: str = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "..",
        "..",
        "tests",
        "identifiers-tests.yml",
    )

    identifiers: list[dict] = AppSettings.lst_from_yml(identifiers_settings_file)
