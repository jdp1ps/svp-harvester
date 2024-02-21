import aiohttp
from aiohttp import ClientError
from aiosparql.client import SPARQLClient
from rdflib import Literal

from app.config import get_app_settings
from app.db.models.concept import Concept as DbConcept
from app.services.concepts.concept_solver_rdf import ConceptSolverRdf
from app.services.concepts.dereferencing_error import DereferencingError


class SparqlJelConceptSolver(ConceptSolverRdf):
    """
    JEL concept solver
    """

    QUERY_TEMPLATE = """
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT ?prefLabel ?altLabel
    WHERE {
      <URI> skos:prefLabel ?prefLabel .
      OPTIONAL {
        <URI> skos:altLabel ?altLabel .
      }
    }
    """

    def get_uri(self, concept_id: str) -> str:
        """
        Concatenate the JEL namespace with the last part of the concept id
        """
        concept_code = concept_id.rsplit(".", 1)[-1]
        return f"http://zbw.eu/beta/external_identifiers/jel#{concept_code}"

    def _get_client(self) -> SPARQLClient:
        settings = get_app_settings()
        assert (
            settings.svp_jel_proxy_url is not None
        ), "SVP_JEL_PROXY_URL environment variable must be set"
        return SPARQLClient(
            settings.svp_jel_proxy_url,
            connector=aiohttp.TCPConnector(limit=0),
            timeout=aiohttp.ClientTimeout(total=300),
        )

    async def solve(self, concept_id: str) -> DbConcept:
        """
        Solves a JEL concept from a concept id
        from a Fuseki endpoint

        :param concept_id: JEL code
        :return: Concept
        """
        query = self.QUERY_TEMPLATE.replace("URI", concept_id)
        client: SPARQLClient = self._get_client()
        try:
            sparql_response = await client.query(query)
            concept = DbConcept(uri=concept_id)
            labels = sparql_response["results"]["bindings"]
            pref_labels = [
                label["prefLabel"]["value"] for label in labels if "prefLabel" in label
            ]
            if not pref_labels:
                raise DereferencingError(
                    f"JEL Sparql endpoint returned no prefLabel while dereferencing {concept_id}"
                )
            self._add_labels(
                concept,
                list(
                    {
                        Literal(
                            label["prefLabel"]["value"],
                            lang=label["prefLabel"]["xml:lang"],
                        )
                        for label in labels
                        if "prefLabel" in label
                    }
                ),
                True,
            )
            self._add_labels(
                concept,
                list(
                    {
                        Literal(
                            label["altLabel"]["value"],
                            lang=label["altLabel"]["xml:lang"],
                        )
                        for label in labels
                        if "altLabel" in label
                    }
                ),
                False,
            )
            return concept
        except ClientError as error:
            raise DereferencingError(
                "Endpoint failure while querying Fuseki sparql endpoint "
                f"{get_app_settings().svp_jel_proxy_url} "
                f"for concept_id {concept_id} with message {error}"
            ) from error
        except Exception as error:
            raise DereferencingError(
                "Unknown error while querying Fuseki sparql endpoint "
                f"{get_app_settings().svp_jel_proxy_url} "
                f"for concept_id {concept_id} with message {error}"
            ) from error
        finally:
            await client.close()
