from typing import List, Dict

from loguru import logger
from lxml import etree


class HalTEIDecoder:
    """
    Wrapper for HAL API TEI (from "base_xml" field) to extract author identifiers.
    """

    def __init__(self, tei_raw_data: str):
        """
        Constructor to initialize with TEI raw data.

        :param tei_raw_data: A string containing the TEI XML data.
        """
        self.tei_raw_data = tei_raw_data
        try:
            self.tree = etree.fromstring(tei_raw_data.encode("utf-8"))
        except etree.XMLSyntaxError as e:
            logger.error(f"TEI XML data are not usable: {e}")
            self.tree = None

    def get_identifiers(self, numeric_id_hal: int) -> List[Dict[str, str]]:
        """
        Given a numeric HAL ID, return a list of identifiers for that specific author.

        :param numeric_id_hal: The numeric HAL ID to search for.
        :return: A list of dictionaries with 'type' and 'value' keys.
        """
        namespace = {"tei": "http://www.tei-c.org/ns/1.0"}
        identifiers = []

        if not self.tree:
            return identifiers  # Return empty if the TEI XML data are not usable

        # XPath to find the specific author with the given numeric HAL ID
        xpath = (
            f"//tei:author[.//tei:idno[@type='idhal'][@notation='numeric' "
            f"and text()='{numeric_id_hal}']]"
        )
        author_elements = self.tree.xpath(xpath, namespaces=namespace)

        if not author_elements:
            return identifiers  # Return empty if no matching author is found

        author = author_elements[0]  # Assuming one unique author matches the ID
        idnos = author.xpath(".//tei:idno", namespaces=namespace)
        for idno in idnos:
            id_type = idno.get("type")
            id_value = idno.text
            if id_type and id_value:
                identifier = self._process_identifier_data(id_type, id_value)
                identifiers.append(identifier)

        return identifiers

    def _process_identifier_data(self, id_type, id_value):
        identifier = {"type": self._normalize(id_type), "value": id_value}
        if id_type == "idhal":
            if id_value.isnumeric():
                identifier["type"] = "idhal_i"
            else:
                identifier["type"] = "idhal_s"
        return identifier

    @staticmethod
    def _normalize(text: str) -> str:
        """
        Normalize the text by converting to lowercase and replacing spaces with underscores.

        :param text: The text to normalize.
        :return: The normalized text.
        """
        return text.lower().replace(" ", "_")
