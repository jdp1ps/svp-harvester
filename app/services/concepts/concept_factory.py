import re
from datetime import datetime

from app.config import get_app_settings
from app.db.models.concept import Concept as DbConcept
from app.services.concepts.abes_concept_solver import AbesConceptSolver
from app.services.concepts.concept_informations import ConceptInformations
from app.services.concepts.concept_solver import ConceptSolver
from app.services.concepts.sparql_idref_concept_solver import SparqlIdRefConceptSolver
from app.services.concepts.skosmos_jel_concept_solver import SkosmosJelConceptSolver
from app.services.concepts.sparql_jel_concept_solver import SparqlJelConceptSolver
from app.services.concepts.unknown_authority_exception import UnknownAuthorityException
from app.services.concepts.wikidata_concept_solver import WikidataConceptSolver


class ConceptFactory:
    """
    Concept factory : solves a concept from a concept id and an optional source
    by calling the appropriate solver
    """

    @staticmethod
    def complete_information(concept_informations: ConceptInformations) -> None:
        """
        Infer additional concept information from provided informations

        :param concept_informations: concept informations
        :return: None
        """
        if concept_informations.source is None:
            ConceptFactory._infer_source(concept_informations)
        solver: ConceptSolver = ConceptFactory._create_solver(
            concept_informations.source
        )
        solver.complete_information(concept_informations)

    @staticmethod
    async def solve(concept_informations: ConceptInformations) -> DbConcept:
        """
        Solves a concept from a concept id and an optional source
        :param concept_informations: concept informations
        :return:
        """
        if concept_informations.source is None:
            # infer source from uri
            ConceptFactory._infer_source(concept_informations)
        # create a solver adapted to the source
        solver: ConceptSolver = ConceptFactory._create_solver(
            concept_informations.source
        )
        # solve the concept
        concept = await solver.solve(concept_informations)
        concept.dereferenced = True
        concept.last_dereferencing_date_time = datetime.now()
        return concept

    @classmethod
    def _create_solver(
        cls, concept_source: ConceptInformations.ConceptSources
    ) -> ConceptSolver:
        settings = get_app_settings()
        if concept_source == ConceptInformations.ConceptSources.IDREF:
            return SparqlIdRefConceptSolver(timeout=settings.idref_concepts_timeout)
        if concept_source == ConceptInformations.ConceptSources.WIKIDATA:
            return WikidataConceptSolver(timeout=settings.wikidata_concepts_timeout)
        if concept_source == ConceptInformations.ConceptSources.JEL:
            if settings.svp_jel_proxy_url is not None:
                return SparqlJelConceptSolver(
                    timeout=settings.sparql_jel_concepts_timeout
                )
            return SkosmosJelConceptSolver(
                timeout=settings.skosmos_jel_concepts_timeout
            )
        if concept_source == ConceptInformations.ConceptSources.ABES:
            return AbesConceptSolver(timeout=settings.abes_concepts_timeout)

        # add more sources here
        # if no solver is found, raise an exception
        raise ValueError(f"Unknown concept source {concept_source}")

    @classmethod
    def _infer_source(
        cls, concept_informations: ConceptInformations
    ) -> ConceptInformations.ConceptSources:
        if concept_informations.uri is not None:
            if cls._idref_pattern().match(concept_informations.uri):
                concept_informations.source = (
                    ConceptInformations.ConceptSources.IDREF
                )  # idref
            elif cls._wikidata_pattern().match(concept_informations.uri):
                concept_informations.source = (
                    ConceptInformations.ConceptSources.WIKIDATA
                )
            elif cls._jel_pattern().match(concept_informations.uri):
                concept_informations.source = ConceptInformations.ConceptSources.JEL
            elif cls._abes_pattern().match(concept_informations.uri):
                concept_informations.source = ConceptInformations.ConceptSources.ABES
            else:
                raise UnknownAuthorityException(concept_informations.uri)
        else:
            raise UnknownAuthorityException(
                concept_informations.code or concept_informations.label
            )

    @classmethod
    def _idref_pattern(cls):
        return re.compile(r"^https?://www\.idref\.fr")

    @classmethod
    def _wikidata_pattern(cls):
        return re.compile(r"^https?://www\.wikidata\.org")

    @classmethod
    def _jel_pattern(cls):
        return re.compile(r"^https?://zbw\.eu")

    @classmethod
    def _abes_pattern(cls):
        return re.compile(r"^https?://hub\.abes\.fr")
