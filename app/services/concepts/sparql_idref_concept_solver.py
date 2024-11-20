import re

from rdflib import Literal

from app.config import get_app_settings
from app.db.models.concept import Concept as DbConcept
from app.harvesters.idref.idref_sparql_client import IdrefSparqlClient
from app.harvesters.idref.idref_sparql_query_builder import (
    IdrefSparqlQueryBuilder as QueryBuilder,
)
from app.services.concepts.concept_informations import ConceptInformations
from app.services.concepts.concept_solver import ConceptSolver
from app.services.concepts.dereferencing_error import DereferencingError


class SparqlIdRefConceptSolver(ConceptSolver):
    """
    IdRef concept solver
    """

    def complete_information(self,
                             concept_informations: ConceptInformations
                             ) -> None:
        # pylint:disable=duplicate-code
        """
        Build url, code and/or uri from concept information
        """
        if concept_informations.uri is None and concept_informations.code is not None:
            concept_informations.uri = (
                f"http://www.idref.fr/{concept_informations.code}/id"
            )
        original_concept_uri = concept_informations.uri
        if concept_informations.uri is not None and concept_informations.code is None:
            match = re.search(
                r"https?://www.idref.fr/(\d+X?)/id", concept_informations.uri
            )
            if match is not None:
                concept_informations.code = match.group(1)
            if concept_informations.code is None:
                raise DereferencingError(
                    f"Unable to extract code from uri {concept_informations.uri}"
                )
        assert (
                concept_informations.code is not None
        ), "Concept information may not be None at this point"
        if not concept_informations.code[0:-1].isdigit():
            raise DereferencingError(
                f"Invalid idref concept id or uri {original_concept_uri}"
            )
        concept_informations.url = (
            f"https://www.idref.fr/{concept_informations.code}.rdf"
        )
        concept_informations.uri = f"http://www.idref.fr/{concept_informations.code}/id"

    async def solve(self, concept_informations: ConceptInformations) -> DbConcept:
        """
        Solve an Idref concept from a concept id
        :param concept_informations:
        :return: Concept
        """
        settings = get_app_settings()
        builder = QueryBuilder()
        builder.set_subject_type(builder.SubjectType.CONCEPT)
        builder.set_subject_uri(concept_informations.uri)
        returned_concept = await IdrefSparqlClient(
            timeout=settings.idref_sparql_timeout
        ).fetch_concept(builder.build())

        concept = DbConcept(uri=concept_informations.uri)

        if 'pref_labels' in returned_concept:
            self._add_labels(
                concept,
                list(
                    {
                        Literal(
                            label["value"],
                            lang=label.get("xml:lang"),
                        )
                        for label in returned_concept["pref_labels"]
                        if "pref_labels" in returned_concept
                    }
                ),
                True,
            )

        if 'alt_labels' in returned_concept:
            self._add_labels(
                concept,
                list(
                    {
                        Literal(
                            label["value"],
                            lang=label.get("xml:lang"),
                        )
                        for label in returned_concept["alt_labels"]
                        if "alt_labels" in returned_concept
                    }
                ),
                False,
            )
        return concept
