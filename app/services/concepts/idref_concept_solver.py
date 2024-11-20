import re

from app.services.concepts.concept_informations import ConceptInformations
from app.services.concepts.dereferencing_error import DereferencingError
from app.services.concepts.rdf_concept_solver import RdfConceptSolver


class IdRefConceptSolver(RdfConceptSolver):
    """
    IdRef concept solver
    """

    def complete_information(self, concept_informations: ConceptInformations) -> None:
        """
        Build url, code and/or uri from concept informations
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
