import re
from xml.sax import SAXParseException

from rdflib import Graph
from rdflib.exceptions import ParserError

from app.harvesters.exceptions.unexpected_format_exception import (
    UnexpectedFormatException,
)
from app.harvesters.idref.resolver_http_client import ResolverHTTPClient
from app.utilities.async_rdf_graph_decorator import AsyncRDFGraphDecorator

DEFAULT_RDF_TIMEOUT = 30


class RdfResolver:
    """
    Async RDF Resolver for various RDF sources
    """

    def __init__(self, timeout: int = DEFAULT_RDF_TIMEOUT):
        self.http_client = ResolverHTTPClient(timeout=timeout)

    async def fetch(self, document_uri: str, output_format: str = "xml") -> Graph:
        """
        Fetch the results from the HAL API

        :param document_uri: the document URI for which to fetch the RDF
        :return: A generator of results
        """
        response_text = await self.http_client.get(document_uri)
        if response_text:
            cleaned_response_text = self._clean_response_text(response_text)

            try:
                graph = await AsyncRDFGraphDecorator().parse(
                    data=cleaned_response_text, rdf_format=output_format
                )
                return graph
            except (ParserError, SAXParseException) as error:
                raise UnexpectedFormatException(
                    f"Error while parsing the RDF from {document_uri} : {cleaned_response_text}"
                ) from error
        raise UnexpectedFormatException(
            f"Empty response from {document_uri} : {response_text}"
        )

    def _clean_response_text(self, response_text: str) -> str:
        """
        Clean the response text by removing empty date fields.

        :param response_text: The raw XML response text
        :return: Cleaned XML response text
        """
        # List of regular expressions to match different empty date field patterns
        empty_patterns = [
            re.compile(r"<dc:date[^>]*></dc:date>"),  # Empty <dc:date> tags
            re.compile(r"<dcterms:date[^>]*?/>"),  # Self-closing <dcterms:date> tags
            # Add more patterns if needed
        ]

        # Remove empty fields based on patterns
        for pattern in empty_patterns:
            # Replace all matches of the pattern with an empty string
            response_text = pattern.sub("", response_text)

        return response_text
