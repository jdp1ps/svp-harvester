from enum import Enum
from urllib.parse import urlencode


class HalApiQueryBuilder:
    """
    This class provides an abstraction to build a query for the HAL API.
    """

    class QueryParameters(Enum):
        """
        Enum for named parameters used in main query
        """

        AUTH_ID_HAL_I = "authIdHal_i"
        AUTH_ID_HAL_S = "authIdHal_s"
        AUTH_ORCID_ID_EXT_ID = "authORCIDIdExt_id"

    DEFAULT_DOC_TYPES = ["*"]

    DEFAULT_FIELDS = [
        "docid",
        "halId_s",
        "*_title_s",
        "*_subTitle_s",
        "*_abstract_s",
        "*_keyword_s",
        "authIdForm_i",
        "authFullNameFormIDPersonIDIDHal_fs",
        "authLastName_s",
        "authFirstName_s",
        "authQuality_s",
        "docType_s",
        "docSubType_s",
        "publicationDate_tdate",
        "publicationDate_s",
        "producedDate_tdate",
        "citationFull_s",
        "citationRef_s",
        "authIdHasStructure_fs",
        "labStructId_i",
        "jel_s",
        "*Id_s",
        "page_s",
        "journalId_i",
        "journalTitle_s",
        "journalIssn_s",
        "journalEissn_s",
        "journalPublisher_s",
        "issue_s",
        "volume_s",
        "bookTitle_s",
        "publisher_s",
        "isbn_s",
        "uri_s",
        "fileMain_s",
        "files_s",
        "publisherLink_s",
        "linkExtUrl_s",
        "label_xml",
    ]

    DEFAULT_SORT_PARAMETER = "halId_s"
    DEFAULT_SORT_DIRECTION = "asc"
    DEFAULT_ROWS = 1000

    def __init__(self) -> None:
        self.identifier_type = None
        self.identifier_value = None
        self.fields = self.DEFAULT_FIELDS
        self.doc_types = self.DEFAULT_DOC_TYPES
        self.sort_parameter = self.DEFAULT_SORT_PARAMETER
        self.sort_direction = self.DEFAULT_SORT_DIRECTION

    def set_query(
        self, identifier_type: QueryParameters, identifier_value: str
    ) -> None:
        """
        Set the field name and value representing the entity for which the query is built.

        :param identifier_type: the name of the field, from the QueryParameters enum
        :param identifier_value: the value of the field
        :return: None
        """
        # check that identifier_type is a valid QueryParameters
        assert identifier_type in self.QueryParameters, "Invalid identifier type"
        self.identifier_type = identifier_type
        self.identifier_value = identifier_value

    def build(self) -> str:
        """
        Main building method, returns a query string for the HAL API.
        :return: a query string
        """
        params = (
            self._query_param()
            | self._cursor_mark_param()
            | self._sort_param()
            | self._rows_param()
            | self._filter_param()
            | self._fields_param()
        )
        return urlencode(params)

    def _query_param(self):
        assert (
            self.identifier_type is not None and self.identifier_value is not None
        ), "Set the query parameters before building the query. "
        # Hal will add random results if the orcid id is not quoted
        # thanks Alessandro Buccheri for the tip
        if self.identifier_type == self.QueryParameters.AUTH_ORCID_ID_EXT_ID:
            self.identifier_value = f'"{self.identifier_value}"'
        return {"q": f"{self.identifier_type.value}:{self.identifier_value}"}

    def _cursor_mark_param(self):
        return {}

    def _sort_param(self):
        return {"sort": f"{self.sort_parameter} {self.sort_direction}"}

    def _filter_param(self):
        return {"fq": f"docType_s:({' OR '.join(self.doc_types)})"}

    def _fields_param(self):
        return {"fl": ",".join(self.fields)}

    def _rows_param(self):
        return {"rows": self.DEFAULT_ROWS}
