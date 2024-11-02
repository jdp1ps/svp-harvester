import asyncio

from rdflib import Graph


class AsyncRDFGraphDecorator:
    def __init__(self):
        self.graph = Graph()

    async def parse(self, data, rdf_format="xml"):
        return await asyncio.to_thread(self.graph.parse, data=data, format=rdf_format)
