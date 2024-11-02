import asyncio
from abc import ABC
from typing import Generator

import aiohttp
import rdflib
from rdflib import SKOS, Graph, term
from rdflib.term import Node

from app.db.models.concept import Concept as DbConcept
from app.services.concepts.concept_informations import ConceptInformations
from app.services.concepts.concept_solver import ConceptSolver
from app.services.concepts.dereferencing_error import DereferencingError
from app.utilities.async_rdf_graph_decorator import AsyncRDFGraphDecorator


class RdfConceptSolver(ConceptSolver, ABC):
    """
    Abstract mother class for concept solvers using RDF
    """

    async def solve(self, concept_informations: ConceptInformations) -> DbConcept:
        """
        Solves a RDF concept from a concept id
        :param concept_informations: concept informations
        :return: Concept
        """
        # pylint: disable=duplicate-code
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=float(self.timeout))
            ) as session:
                async with session.get(concept_informations.url) as response:
                    if not 200 <= response.status < 300:
                        raise DereferencingError(
                            f"Endpoint returned status {response.status}"
                            f" while dereferencing RDF concept {concept_informations.uri}"
                            f" at url {concept_informations.url}"
                        )
                    xml = (await response.text()).strip()
                    concept_graph = await AsyncRDFGraphDecorator().parse(
                        data=xml, rdf_format="xml"
                    )
                    concept = DbConcept(uri=concept_informations.uri)

                    self._add_labels(
                        concept=concept,
                        labels=list(
                            self._pref_labels(concept_graph, concept_informations.uri)
                        ),
                        preferred=True,
                    )
                    self._add_labels(
                        concept=concept,
                        labels=list(
                            self._alt_labels(concept_graph, concept_informations.uri)
                        ),
                        preferred=False,
                    )
                    return concept
        except aiohttp.ClientError as error:
            raise DereferencingError(
                f"Endpoint failure while dereferencing {concept_informations.uri} "
                f"at url {concept_informations.url} with message {error}"
            ) from error
        except rdflib.exceptions.ParserError as error:
            raise DereferencingError(
                f"Error while parsing xml from {concept_informations.url} with message {error}"
            ) from error
        except asyncio.exceptions.TimeoutError as error:
            raise DereferencingError(
                f"Timeout while dereferencing {concept_informations.uri}"
                f"at url {concept_informations.url}"
            ) from error
        except Exception as error:
            raise DereferencingError(
                f"Unknown error while dereferencing {concept_informations.uri}"
                f"at url {concept_informations.url} with message {error}"
            ) from error

    def _get_labels(
        self, concept_data: Graph, uri: str, label_type: term.URIRef
    ) -> Generator[Node, None, None]:
        """
        Get labels from a concept graph based on the given label type
        :param concept_data: concept graph
        :param uri: concept uri
        :param label_type: SKOS prefLabel or altLabel

        :return: labels
        """
        return concept_data.objects(term.URIRef(uri), label_type)

    def _pref_labels(
        self, concept_data: Graph, uri: str
    ) -> Generator[Node, None, None]:
        """
        Get preferred labels from a concept graph
        :param concept_data: concept graph
        :param uri: concept uri

        :return: preferred labels
        """
        return self._get_labels(concept_data, uri, SKOS.prefLabel)

    def _alt_labels(self, concept_data: Graph, uri: str) -> Generator[Node, None, None]:
        """
        Get alternative labels from a concept graph
        :param concept_data: concept graph
        :param uri: concept uri

        :return: alternative labels
        """
        return self._get_labels(concept_data, uri, SKOS.altLabel)
