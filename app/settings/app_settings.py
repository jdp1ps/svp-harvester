"""
App settings base class
"""

import os
from typing import ClassVar, TextIO

import yaml
from pydantic_settings import BaseSettings

from app.settings.app_env_types import AppEnvTypes


class AppSettings(BaseSettings):
    """
    App settings main class with parameters definition
    """

    @staticmethod
    def settings_file_path(filename: str) -> str:
        """
        Get the path of a settings file

        :param filename: The name of the settings file
        :return: The path of the settings file
        """
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "..", "..", filename
        )

    @staticmethod
    def lst_from_yml(yml_file: str) -> list[dict]:
        """
        Load settings from yml file
        """
        with open(yml_file, encoding="utf8") as file:
            return yaml.load(file, Loader=yaml.FullLoader)

    app_env: AppEnvTypes = AppEnvTypes.PROD
    debug: bool = False
    logger_sink: ClassVar[str | TextIO] = "logs/app.log"

    api_host: str = "http://localhost:8000"
    api_prefix: str = "/api"
    api_version: str = "v0"

    amqp_enabled: bool = True

    amqp_user: str = "guest"
    amqp_password: str = "guest"
    amqp_host: str = "127.0.0.1"
    amqp_queue_name: str = "svp-harvester"
    amqp_wait_before_shutdown: int = 30
    amqp_task_parallelism_limit: int = 5
    amqp_exchange_name: str = "publications"
    amqp_prefetch_count: int = 5
    amqp_consumer_ack_timeout: int = 180000
    amqp_retrieval_routing_key: str = "task.entity.references.retrieval"
    amqp_reference_event_routing_key: str = "event.references.reference.*"
    amqp_harvesting_event_routing_key: str = "event.references.harvesting.state"
    amqp_retrieval_event_routing_key: str = "event.references.retrieval.state"

    harvesters_settings_file: str = settings_file_path(filename="harvesters.yml")
    harvesters: list = lst_from_yml(yml_file=harvesters_settings_file)

    identifiers_settings_file: str = settings_file_path(filename="identifiers.yml")
    identifiers: list = lst_from_yml(yml_file=identifiers_settings_file)

    jobs_settings_file: str = settings_file_path(filename="jobs.yml")
    jobs: list = lst_from_yml(yml_file=jobs_settings_file)

    db_engine: str = "postgresql+asyncpg"
    db_name: str = "svp_harvester"
    db_user: str = "svp_harvester"
    db_password: str = "secret"
    db_host: str = "localhost"
    db_port: int = 5432
    db_pool_size: int = 20
    max_overflow: int = 10

    scanr_es_host: str = "https://host_name.com/"
    scanr_es_user: str = "johndoe"
    scanr_es_password: str = "pass"

    # when solving SKOS concepts from identifiers, fetch labels in these languages if possible
    concept_languages: list = ["fr", "en"]
    # refresh concepts from identifiers if older than this number of days
    concept_expiration_days: dict = {
        "WIKIDATA": 30,
        "IDREF": 30,
    }

    svp_jel_proxy_url: str | None = None

    scopus_api_key: str = "None"
    scopus_inst_token: str = "None"

    idref_sudoc_timeout: int = 10
    idref_science_plus_timeout: int = 10
    idref_concepts_timeout: int = 10
    wikidata_concepts_timeout: int = 10
    sparql_jel_concepts_timeout: int = 10
    skosmos_jel_concepts_timeout: int = 20
    abes_concepts_timeout: int = 10
    idref_sparql_timeout: int = 10
    hal_organizations_timeout: int = 7
    idref_organizations_timeout: int = 10
    ror_organizations_timeout: int = 7
    scopus_organizations_timeout: int = 5

    third_api_caching_enabled: bool = True
    third_api_default_caching_duration: int = 24 * 3600
    redis_url: str = "redis://localhost:6379"
    redis_max_connections: int = 1000

    sudoc_publications_caching_duration: int = 15 * 24 * 3600
    science_plus_publications_caching_duration: int = 15 * 24 * 3600
    persee_publications_caching_duration: int = 15 * 24 * 3600
    open_edition_publications_caching_duration: int = 15 * 24 * 3600
    idref_concepts_publications_caching_duration: int = 90 * 24 * 3600
    wikidata_concepts_publications_caching_duration: int = 90 * 24 * 3600

    institution_name: str = "XYZ University"

    git_commit: str = "-"
    git_branch: str = "-"
    docker_digest: str = "-"
