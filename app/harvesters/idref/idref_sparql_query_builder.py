from enum import Enum

import uritools
from aiosparql.syntax import Namespace, PrefixedName, IRI

MARCREL_ROLES_LIST = [
    "aut",
    "cmp",
    "ths",
    "edt",
    "pbd",
    "trl",
    "aui",
    "drt",
    "opn",
    "ill",
    "prt",
    "mus",
    "pra",
    "clb",
    "act",
    "ctb",
    "sng",
    "fmo",
    "cnd",
    "ant",
    "sec",
    "sce",
    "ive",
    "pbl",
    "pht",
    "exp",
    "auc",
    "ctg",
    "com",
    "nrt",
    "dte",
    "dnr",
    "art",
    "egr",
    "adp",
    "cur",
    "cwt",
    "bsl",
    "aft",
    "mte",
    "asn",
    "prf",
    "lbt",
    "arr",
    "ivr",
    "rth",
    "dgc",
    "dub",
    "aqt",
    "grt",
    "ccp",
    "cmm",
    "pro",
    "rcp",
    "orm",
    "osp",
    "lyr",
    "ann",
    "prd",
    "flm",
    "sad",
    "wde",
    "dto",
    "aus",
    "ltg",
    "spn",
    "chr",
    "col",
    "rtm",
    "bkd",
    "dnc",
    "etr",
    "res",
    "bnd",
    "pop",
    "rce",
    "voc",
    "pfr",
    "ilu",
    "ins",
    "org",
    "hnr",
    "prg",
    "crr",
    "cll",
    "bpd",
    "pdr",
    "anm",
    "csp",
    "wam",
    "dgg",
    "rev",
    "tyd",
    "dst",
    "scr",
    "sll",
    "isb",
    "tyg",
    "cns",
    "bdd",
    "lso",
    "sgn",
    "lse",
    "bjd",
    "scl",
    "asg",
    "frg",
    "mon",
    "cph",
    "ppm",
    "stm",
    "ppt",
    "rbr",
    "cmt",
    "inv",
    "unknow",
    "oth",
    "pth",
]


class IdrefSparqlQueryBuilder:
    """
    This class provides an abstraction to build a query for data.idref.fr sparql endpoint
    """

    class SubjectType(Enum):
        """
        Types of subjects for which data can be retrieved from data.idref.fr
        """

        PERSON = "person"
        PUBLICATION = "publication"
        CONCEPT = "concept"

    class Marcrel(Namespace):
        """
        MARC relator codes
        """

        __iri__ = IRI("http://id.loc.gov/vocabulary/relators/")
        author = PrefixedName

    def __init__(self) -> None:
        self.subject_uri: str | None = None
        self.orcid: str | None = None
        self.subject_type: IdrefSparqlQueryBuilder.SubjectType | None = None

    def set_idref_id(self, idref_id: str):
        """
        Set the subject uri from an idref id

        :param idref_id: the idref id of the subject
        :return: the query builder
        """
        self.subject_uri = f"http://www.idref.fr/{idref_id}/id"
        return self

    def set_orcid(self, orcid: str):
        """
        Set the orcid

        :param orcid: the orcid of the subject
        :return: the query builder
        """
        self.orcid = orcid
        return self

    def set_subject_type(self, subject_type: SubjectType):
        """
        Set the type of subject about which data will be retrieved : person, publication or concept
        :param subject_type: the type of subject
        :return: the query builder
        """
        self.subject_type = subject_type
        return self

    def set_subject_uri(self, subject_uri: str):
        """
        Disrectly set the subject uri
        :param subject_uri: the subject uri
        :return: the query builder
        """
        assert uritools.isuri(subject_uri), f"{subject_uri} is not a valid URI"
        self.subject_uri = subject_uri
        return self

    def build(self):
        """
        Build the SPARQL query
        :return: the query
        """
        assert (
            self.subject_type is not None
        ), "Specify a subject type before building the query"
        assert self.subject_uri is not None or self.orcid is not None, (
            "Specify an orcid or an idref id for the subject "
            "before building the query"
        )
        if self.subject_type == IdrefSparqlQueryBuilder.SubjectType.PERSON:
            return self._build_person_query()
        if self.subject_type == IdrefSparqlQueryBuilder.SubjectType.PUBLICATION:
            return self._build_publication_query()
        if self.subject_type == IdrefSparqlQueryBuilder.SubjectType.CONCEPT:
            return self._build_concept_query()
        raise ValueError(f"Unknown subject type {self.subject_type}")

    def _build_person_query(self) -> str:
        roles_filter_str = " || ".join(
            f"STR(?contributorRole) = STR(marcrel:{role})"
            for role in MARCREL_ROLES_LIST
        )

        return (
            "PREFIX skos: <http://www.w3.org/2004/02/skos/core#> \n"
            "PREFIX dc: <http://purl.org/dc/elements/1.1/> \n"
            "PREFIX dcterms: <http://purl.org/dc/terms/> \n"
            "PREFIX rdam: <http://rdaregistry.info/Elements/m/> \n"
            "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> \n"
            "PREFIX bibo: <http://purl.org/ontology/bibo/> \n"
            "PREFIX marcrel: <http://id.loc.gov/vocabulary/relators/> \n"
            "select distinct  ?pub ?role ?type ?title ?altLabel ?note "
            "?contributor ?contributorRole ?contributorName "
            "?contributorFamilyName ?contributorGivenName \n"
            "?subject_uri ?subject_label ?doi ?equivalent \n "
            f"where {{ {self._person_sparql_filter()} \n"
            "OPTIONAL {"
            "?pub rdf:type ?type \n"
            "} . "
            "OPTIONAL {"
            "?pub bibo:doi ?doi"
            "} . "
            "OPTIONAL {"
            "?equivalent rdam:P30135 ?pub \n"
            "} . "
            "OPTIONAL {"
            "?pub ?contributorRole ?contributor . "
            "?contributor a foaf:Person . "
            "?contributor foaf:name ?contributorName . "
            "?contributor foaf:familyName ?contributorFamilyName . "
            "?contributor foaf:givenName ?contributorGivenName . "
            # Dynamic version would be better
            # but is too slow : "FILTER(STRSTARTS(STR(?contributorRole), STR(marcrel:))) ."
            f"FILTER({roles_filter_str}) . "
            "} . "
            "OPTIONAL {"
            "?pub dc:title ?title"
            "} . "
            "OPTIONAL {"
            "?pub skos:altLabel ?altLabel"
            "} . "
            "OPTIONAL {"
            "?pub skos:note ?note"
            "} . "
            "OPTIONAL {"
            "?pub dcterms:subject ?subject_uri . "
            "?subject_uri skos:prefLabel ?subject_label "
            "} . "
            "}\n"
            "LIMIT 10000"
        )

    def _build_publication_query(self) -> str:
        return (
            "select distinct ?prop ?val "  # caution: trailing space is important
            f"where {{<{self.subject_uri}> ?prop ?val}}\n"
            "LIMIT 10000"
        )

    def _build_concept_query(self) -> str:
        return (
            "PREFIX skos: <http://www.w3.org/2004/02/skos/core#> "
            "select distinct ?prefLabel ?altLabel "
            "where { "
            f"<{self.subject_uri}> a skos:Concept. "
            f"OPTIONAL {{<{self.subject_uri}> skos:prefLabel ?prefLabel}}. "
            f"OPTIONAL {{<{self.subject_uri}> skos:altLabel ?altLabel}} "
            "} "
            "LIMIT 100"
        )

    def _person_sparql_filter(self):
        if self.subject_uri is not None:
            return f"?pub ?role <{self.subject_uri}> ."
        if self.orcid is not None:
            return f"?pub ?role ?pers . \n" f'?pers vivo:orcidId "{self.orcid}" .'
        raise ValueError("Specify an orcid or an idref id for the subject")
