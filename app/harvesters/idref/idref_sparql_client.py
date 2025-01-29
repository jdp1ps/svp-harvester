from enum import Enum
from typing import AsyncGenerator

import aiohttp
from aiosparql.client import SPARQLClient

from app.harvesters.exceptions.external_endpoint_failure import ExternalEndpointFailure
from app.utilities.execution_timer_wrapper import execution_timer

DATA_IDREF_FR_URL = "https://data.idref.fr/sparql"

IDREF_SPARQL_DEFAULT_TIMEOUT = 20


class IdrefSparqlClient:
    """Async client for data.idref.fr SPARQL API, wrapper around aiosparql"""

    def __init__(self, timeout: int = IDREF_SPARQL_DEFAULT_TIMEOUT):
        self.timeout = timeout

    class DataSources(Enum):
        """Typology of data sources for which data.idref.fr gathers data"""

        IDREF = "IDREF"
        HAL = "HAL"
        SUDOC = "SUDOC"
        SCIENCE_PLUS = "SCIENCE_PLUS"
        OPEN_EDITION = "OPEN_EDITION"
        PERSEE = "PERSEE"

    AUTHORS_PREFIXES = [
        "http://id.loc.gov/vocabulary/relators/",
        "http://www.abes.fr/vocabularies/theses/roles/",
    ]

    DATA_SOURCES_PREFIXES = {
        DataSources.IDREF: [
            "http://www.idref.fr/",
        ],
        DataSources.HAL: [
            "https://hal.archives-ouvertes.fr/",
        ],
        DataSources.SUDOC: [
            "http://www.sudoc.fr/",
        ],
        DataSources.SCIENCE_PLUS: [
            "http://hub.abes.fr/",
        ],
        DataSources.OPEN_EDITION: [
            "http://journals.openedition.org/",
            "https://journals.openedition.org/",
            "http://books.openedition.org/",
            "https://books.openedition.org/",
        ],
        DataSources.PERSEE: [
            "http://data.persee.fr/",
        ],
    }

    @execution_timer
    async def fetch_publications(self, query: str) -> AsyncGenerator[dict, None]:
        """
        Fetch publications list for a given author from the Idref sparql endpoint.

        :param query: The sparql query to send to the Idref sparql endpoint.
        :return: A generator of results.
        """
        client: SPARQLClient = self._get_client()
        try:
            response = await client.query(query)
            # Aggregate results
            publications = {}
            for result in response.get("results", {}).get("bindings", []):
                if not any(
                    result.get("role", {}).get("value", "").startswith(prefix)
                    for prefix in self.AUTHORS_PREFIXES
                ):
                    continue
                pub = result.get("pub", {}).get("value", "")
                # Create a new publication if it does not exist
                if pub not in publications:
                    publications[pub] = {
                        "uri": pub,
                        "role": result.get("role", {}).get("value", ""),
                        "date": result.get("date", {}).get("value", ""),
                        "contributors": {},  # Use a dictionary for contributors
                        "title": [],
                        "note": [],
                        "type": [],
                        "altLabel": [],
                        "subject": {},
                        "equivalent": [],
                        "doi": result.get("doi", {}).get("value", ""),
                    }
                # Add or update the contributor data
                contributor_uri = result.get("contributor", {}).get("value", "")
                if contributor_uri:
                    if contributor_uri not in publications[pub]["contributors"]:
                        publications[pub]["contributors"][contributor_uri] = {
                            "name": result.get("contributorName", {}).get("value", ""),
                            "familyName": result.get("contributorFamilyName", {}).get(
                                "value", ""
                            ),
                            "givenName": result.get("contributorGivenName", {}).get(
                                "value", ""
                            ),
                            "roles": [],  # Initialize roles as a list
                        }
                    # Add the role to the contributor if not already present
                    role = result.get("contributorRole", {}).get("value", "")
                    if (
                        role
                        and role
                        not in publications[pub]["contributors"][contributor_uri][
                            "roles"
                        ]
                    ):
                        publications[pub]["contributors"][contributor_uri][
                            "roles"
                        ].append(role)

                # Add other data to the publication
                for key in ["type", "title", "altLabel", "note", "equivalent"]:
                    if (
                        result.get(key, {}).get("value", "")
                        not in publications[pub][key]
                    ):
                        publications[pub][key].append(
                            result.get(key, {}).get("value", "")
                        )
                subject_uri = result.get("subject_uri", {}).get("value", "")
                if subject_uri and subject_uri not in publications[pub]["subject"]:
                    publications[pub]["subject"][subject_uri] = {
                        "uri": subject_uri,
                        "label": result.get("subject_label", {}).get("value", ""),
                        "lang": result.get("subject_label", {}).get("xml:lang", ""),
                    }

            for publication in publications.values():
                yield publication | {
                    # identify the secondary source to which the publication belongs
                    "secondary_source": self._result_source_code(
                        publication.get("uri", "")
                    )
                }
        except Exception as error:
            raise ExternalEndpointFailure(
                "Error while fetching Idref sparql endpoint for query : "
                f"{query} with error {error.__class__.__name__} {error if error else ''}"
            ) from error

        finally:
            await client.close()

    @execution_timer
    async def fetch_publication(self, query: str) -> dict:
        """
        Fetch data for a single publication from the Idref sparql endpoint
        :param query: the sparql query to send to the Idref sparql endpoint
        :return: the result as dict
        """
        client: SPARQLClient = self._get_client()
        try:
            response = await client.query(query)
            print(query)
            pub_raw_data: dict = response.get("results", {}).get("bindings", [])
            # simplify the data structure by removing the first level of keys
            return {
                data.get("prop", {})
                .get("value", ""): data.get("val", {})
                .get("value", "")
                for data in pub_raw_data
            }
        except Exception as error:
            raise ExternalEndpointFailure(
                "Error while fetching Idref sparql endpoint for query : "
                f"{query} with error {error.__class__.__name__} {error if error else ''}"
            ) from error
        finally:
            await client.close()

    async def fetch_concept(self, query: str) -> dict:
        """
        Fetch data for a single concept from the Idref sparql endpoint
        :param query: the sparql query to send to the Idref sparql endpoint
        :return: the result as dict
        """
        client: SPARQLClient = self._get_client()

        try:
            response = await client.query(query)
            concept_raw_data: dict = response.get("results", {}).get("bindings", [])
            dict_to_return = {}

            if any("prefLabel" in entry for entry in concept_raw_data):
                unique_pref_labels = {
                    tuple(label.items())
                    for label in (entry.get("prefLabel") for entry in concept_raw_data)
                }
                dict_to_return["pref_labels"] = [
                    dict(label) for label in unique_pref_labels
                ]

            if any("altLabel" in entry for entry in concept_raw_data):
                unique_alt_labels = {
                    tuple(label.items())
                    for label in (entry.get("altLabel") for entry in concept_raw_data)
                }
                dict_to_return["alt_labels"] = [
                    dict(label) for label in unique_alt_labels
                ]

            return dict_to_return
        except Exception as error:
            raise ExternalEndpointFailure(
                "Error while fetching Idref sparql endpoint for query : "
                f"{query} with error {error.__class__.__name__} {error if error else ''}"
            ) from error
        finally:
            await client.close()

    def _result_source_code(self, uri: str) -> str:
        for source, prefixes in self.DATA_SOURCES_PREFIXES.items():
            if any(uri.startswith(prefix) for prefix in prefixes):
                return source.value
        raise ExternalEndpointFailure(f"Unknown data source for uri {uri}")

    def _get_client(self) -> SPARQLClient:
        return SPARQLClient(
            DATA_IDREF_FR_URL,
            connector=aiohttp.TCPConnector(limit=0),
            timeout=aiohttp.ClientTimeout(total=float(self.timeout)),
        )
