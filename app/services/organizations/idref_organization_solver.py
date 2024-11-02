import asyncio
import re
from typing import List
from typing import Tuple

import aiohttp
from rdflib import OWL, term

from app.db.models.organization import Organization
from app.db.models.organization_identifier import OrganizationIdentifier
from app.services.concepts.dereferencing_error import DereferencingError
from app.services.organizations import (  # pylint: disable=cyclic-import
    organization_factory,
)
from app.services.organizations.organization_data_class import OrganizationInformations
from app.services.organizations.organization_solver import OrganizationSolver
from app.utilities.async_rdf_graph_decorator import AsyncRDFGraphDecorator


# pylint: disable=duplicate-code
class IdrefOrganizationSolver(OrganizationSolver):
    """
    Hal organization solver
    """

    URL = "www.idref.fr/"
    # value could be 'ror'
    IDENTITY_DEEP_SEARCH = []
    IDENTITY_SAVE = ["hal", "isni", "viaf", "ror"]

    async def solve(
        self, organization_information: OrganizationInformations
    ) -> Organization:
        """
        Solves an organization from an organization id
        :param organization_id: id of the organization
        :return: organization
        """
        raise NotImplementedError("IdrefOrganizationSolver.solve")

    async def solve_identities(
        self, organization_information: OrganizationInformations, seen: List[str]
    ) -> tuple[List[OrganizationIdentifier], List[str]]:
        """
        Solves the identities of an organization and search for more identifiers
        :param organization: organization
        :return: OrganizationIdentifier, seen identifiers updated list
        """

        # Add the idref identifier
        new_identifiers = [
            OrganizationIdentifier(
                type="idref", value=organization_information.identifier
            )
        ]
        seen.append("idref")
        # Search for more identifiers
        idref_url, idref_uri = self._build_url_from_organization_id(
            organization_information.identifier
        )
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=float(self.timeout))
            ) as session:
                async with session.get(idref_url) as response:
                    if not 200 <= response.status < 300:
                        raise DereferencingError(
                            f"Endpoint returned status {response.status}"
                            f" while dereferencing {idref_url}"
                        )
                    xml = await response.text()
                    concept_graph = await AsyncRDFGraphDecorator().parse(
                        data=xml, rdf_format="xml"
                    )
                    # Search for sameAs identifiers
                    for uri in concept_graph.objects(
                        term.URIRef(idref_uri), OWL.sameAs
                    ):
                        source, identifier = self._infer_source_and_id_from_uri(uri)

                        if source in seen or (source is None and identifier is None):
                            continue
                        try:
                            if source in self.IDENTITY_DEEP_SEARCH:
                                (
                                    identifiers,
                                    seen,
                                ) = await organization_factory.OrganizationFactory.solve_identities(
                                    OrganizationInformations(
                                        identifier=identifier, source=source
                                    ),
                                    seen,
                                )
                                new_identifiers.extend(identifiers)
                            elif source in self.IDENTITY_SAVE:
                                new_identifiers.append(
                                    OrganizationIdentifier(
                                        type=source, value=identifier
                                    )
                                )
                                seen.append(source)
                        except ValueError:
                            new_identifiers.append(
                                OrganizationIdentifier(type=source, value=identifier)
                            )
                            seen.append(source)
                    return new_identifiers, seen

        # If the request fails, return the new identifiers with only the idref identifier
        except aiohttp.ClientError:
            return new_identifiers, seen
        except asyncio.TimeoutError:
            return new_identifiers, seen

    def _build_url_from_organization_id(self, organization_id):
        uri = f"http://{self.URL}{organization_id}/id"
        url = f"https://{self.URL}{organization_id}.rdf"
        return url, uri

    def _infer_source_and_id_from_uri(self, uri) -> Tuple[str, str]:
        uri = re.sub(r"https?://", "", uri)
        if "data.archives-ouvertes.fr" in uri:
            return "hal", uri.split("/")[-1].replace("#foaf:Organization", "")
        if "ror.org" in uri:
            return "ror", uri.split("/")[-1].replace("#foaf:Organization", "")
        if "isni.org" in uri:
            return "isni", uri.split("/")[-1]
        if "viaf.org" in uri:
            return "viaf", uri.split("/")[-1]
        return None, None
