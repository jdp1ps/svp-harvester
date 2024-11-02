from asyncio.exceptions import TimeoutError as AsyncTimeoutError

import aiohttp

from app.harvesters.exceptions.external_endpoint_failure import ExternalEndpointFailure


class ResolverHTTPClient:
    """
    Generic HTTP client for resolving URIs
    """

    def __init__(self, timeout: int = 30):
        self.connector = aiohttp.TCPConnector(limit=0)
        self.timeout = timeout

    async def get(self, document_url: str) -> str:
        """
        Get any document from remote URL as text

        :param document_url: the URL to fetch
        :return: the document as text
        """
        try:
            async with aiohttp.ClientSession(
                connector=self.connector,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as session:
                async with session.get(document_url) as resp:
                    if resp.status == 200:
                        return await resp.text()
                    raise ExternalEndpointFailure(
                        f"Error code while resolving URI : {document_url} "
                        f"with code {resp.status}"
                    )
        except aiohttp.ClientConnectorError as error:
            raise ExternalEndpointFailure(
                f"Cant resolve URI : {document_url} with error {error}"
            ) from error
        except AsyncTimeoutError as error:
            raise ExternalEndpointFailure(
                f"Timeout while resolving URI : {document_url}"
            ) from error
        except Exception as error:
            raise ExternalEndpointFailure(
                f"Error while resolving URI : {document_url} with error {error}"
            ) from error
