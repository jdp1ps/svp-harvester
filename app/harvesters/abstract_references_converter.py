import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import wraps
from typing import List, AsyncGenerator

from loguru import logger
from semver import Version
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.db.daos.book_dao import BookDAO
from app.db.daos.concept_dao import ConceptDAO
from app.db.daos.contributor_dao import ContributorDAO
from app.db.daos.document_type_dao import DocumentTypeDAO
from app.db.daos.issue_dao import IssueDAO
from app.db.daos.journal_dao import JournalDAO
from app.db.daos.organization_dao import OrganizationDAO
from app.db.models.book import Book
from app.db.models.concept import Concept
from app.db.models.contribution import Contribution
from app.db.models.contributor import Contributor
from app.db.models.document_type import DocumentType
from app.db.models.issue import Issue
from app.db.models.journal import Journal
from app.db.models.label import Label
from app.db.models.organization import Organization
from app.db.models.reference import Reference
from app.db.session import async_session
from app.harvesters.abstract_harvester_raw_result import AbstractHarvesterRawResult
from app.services.book.book_data_class import BookInformations
from app.services.concepts.concept_factory import ConceptFactory
from app.services.concepts.concept_informations import ConceptInformations
from app.services.concepts.dereferencing_error import DereferencingError
from app.services.hash.hash_key import HashKey
from app.services.hash.hash_service import HashService
from app.services.issue.issue_data_class import IssueInformations
from app.services.journal.journal_data_class import JournalInformations
from app.services.organizations.merge_organization import merge_organization
from app.services.organizations.organization_data_class import OrganizationInformations
from app.services.organizations.organization_factory import OrganizationFactory
from app.utilities.execution_timer_wrapper import execution_timer


class AbstractReferencesConverter(ABC):
    """ "
    Abstract mother class for harvesters
    """

    reference_non_empty_lists_fields: list[str] = ["titles"]
    reference_non_blank_string_fields: list[str] = ["harvester"]
    reference_not_null_fields: list[str] = [
        "abstracts",
        "subtitles",
        "subjects",
        "document_type",
        "contributions",
    ]

    @dataclass
    class ContributionInformations:
        """
        Informations about a contribution
        """

        role: str | None = Contribution.get_url("UNKNOWN")
        rank: int | None = None
        name: str | None = None
        identifier: str | None = None
        ext_identifiers: List[dict[str, str]] = None

    async def _contributions(
        self,
        contribution_informations: List[ContributionInformations],
        source: str,
    ) -> AsyncGenerator[Contribution, None]:
        # if a contributor duplicate was created inside the loop, unicity rules
        # would apply only later and the whole reference would fail to be
        # created in database. To avoid this, we use a cache to store contributors
        # already created and avoid duplicates.
        # A duplicate is an identifiers duplicate for contributors with an identifier
        # or a name duplicate for contributors without an identifier.
        contributors_identifiers_cache = {}
        contributors_names_cache = {}
        for contribution_information in contribution_informations:
            identifier = contribution_information.identifier
            name = contribution_information.name
            ext_identifiers = contribution_information.ext_identifiers
            assert (
                identifier is not None or name is not None
            ), "No identifier or name provided for contributor"
            if identifier is not None:
                db_contributor = contributors_identifiers_cache.get(identifier)
            else:
                db_contributor = contributors_names_cache.get(name)
            if db_contributor is None:
                if identifier is not None:
                    db_contributor = (
                        await self._get_or_create_contributor_by_identifier(
                            source=source, source_identifier=identifier, name=name
                        )
                    )
                    self._update_contributor_name(db_contributor, name)
                    await self._update_contributor_external_identifiers(
                        db_contributor, ext_identifiers
                    )
                else:
                    db_contributor = await self._get_or_create_contributor_by_name(
                        source=source, name=name
                    )
                if identifier is not None:
                    contributors_identifiers_cache[identifier] = db_contributor
                else:
                    contributors_names_cache[name] = db_contributor

            yield Contribution(
                contributor=db_contributor,
                role=contribution_information.role,
                rank=contribution_information.rank,
            )

    async def _update_contributor_external_identifiers(
        self, db_contributor: Contributor, ext_identifiers: List[dict[str, str]]
    ):
        """
        Update the external identifiers of the contributor
        """
        async with async_session() as session:
            async with session.begin():
                await ContributorDAO(session).update_external_identifiers(
                    db_contributor.id, ext_identifiers
                )

    @staticmethod
    def validate_reference(func):
        """
        Decorator to validate the reference object content before returning it
        """

        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            ref = kwargs["new_ref"]
            await func(self, *args, **kwargs)
            assert ref.source_identifier is not None, (
                f"Validation failed in method {self.__class__.__name__}.{func.__name__}"
                f" Source identifier should be set on reference"
            )

            failed_fields = []
            for field in self.reference_non_empty_lists_fields:
                if (
                    not isinstance(getattr(ref, field), list)
                    or len(getattr(ref, field)) == 0
                ):
                    failed_fields.append(field)
            for field in self.reference_non_blank_string_fields:
                if (
                    not isinstance(getattr(ref, field), str)
                    or not getattr(ref, field).strip()
                ):
                    failed_fields.append(field)
            for field in self.reference_not_null_fields:
                if getattr(ref, field) is None:
                    failed_fields.append(field)

            if failed_fields:
                assert False, (
                    f"Validation failed in method {self.__class__.__name__}.{func.__name__}"
                    f" for reference: {ref.source_identifier}."
                    f" {', '.join(failed_fields)} should be set on reference"
                )

        return wrapper

    def build(
        self, raw_data: AbstractHarvesterRawResult, harvester_version: Version
    ) -> Reference:
        """
        Build a Normalised Reference object with basic information
        :param raw_data: Raw data from harvester source
        :param harvester_version: version of the harvester
        :return: Normalised Reference object with basic information
        """
        new_ref = Reference()
        new_ref.harvester = self._harvester()
        new_ref.source_identifier = str(raw_data.source_identifier)
        new_ref.harvester_version = str(harvester_version)
        new_ref.hash = self.compute_hash(
            raw_data=raw_data, harvester_version=harvester_version
        )
        return new_ref

    def compute_hash(
        self, raw_data: AbstractHarvesterRawResult, harvester_version: Version
    ) -> str:
        """
        Compute the hash of the raw data
        :param raw_data: raw data from harvester source
        :param harvester_version: version of the harvester
        :return:
        """
        return HashService().hash(
            raw_data=raw_data, hash_dict=self.hash_keys(harvester_version)
        )

    @abstractmethod
    def _harvester(self) -> str:
        raise NotImplementedError

    @validate_reference
    @abstractmethod
    async def convert(self, raw_data: AbstractHarvesterRawResult, new_ref: Reference):
        """
        Populates raw data from harvester source to the normalised Reference object
        :param raw_data: Raw data from harvester source
        :param new_ref: Reference object with basic information
        :return: Normalised Reference object with basic information
        """

    def hash_keys(self, harvester_version: Version) -> list[HashKey]:
        """
        For the most simple case where data to hash are a dictionary,
        returns the keys of the dictionary to include in change detection
        :return: a list of keys
        """
        raise NotImplementedError

    async def _get_or_create_contributor_by_name(
        self, source: str, name: str, new_attempt: bool = False
    ):
        async with async_session() as session:
            async with session.begin_nested():
                contributor = await ContributorDAO(session).get_by_source_and_name(
                    source=source, name=name
                )
                if contributor is None:
                    contributor = Contributor(
                        source=source,
                        source_identifier=None,
                        name=name,
                    )
                    session.add(contributor)
                    try:
                        await session.commit()
                    except IntegrityError as error:
                        # The concept has been created by another process,
                        # during resolution process,
                        # so rollback the current transaction
                        # and get the concept from the database
                        assert new_attempt is False, (
                            f"Unique name {name} violation "
                            "for contributor without uri cannot occur twice"
                            f" during concept creation : {error}"
                        )
                        await session.rollback()
                        contributor = await self._get_or_create_contributor_by_name(
                            source=source, name=name, new_attempt=True
                        )
        return contributor

    async def _get_or_create_contributor_by_identifier(
        self,
        source: str,
        source_identifier: str,
        name: str,
        new_attempt: bool = False,
    ):
        async with async_session() as session:
            async with session.begin_nested():
                contributor = await ContributorDAO(
                    session
                ).get_by_source_and_identifier(
                    source=source, source_identifier=source_identifier
                )
                if contributor is None:
                    contributor = Contributor(
                        source=source,
                        source_identifier=source_identifier,
                        name=name,
                    )
                    session.add(contributor)
                    try:
                        await session.commit()
                    except IntegrityError as error:
                        assert new_attempt is False, (
                            f"Unique identifier {source_identifier} violation "
                            "for contributor cannot occur twice "
                            f"during concept creation : {error}"
                        )
                        await session.rollback()
                        contributor = (
                            await self._get_or_create_contributor_by_identifier(
                                source=source,
                                source_identifier=source_identifier,
                                name=name,
                                new_attempt=True,
                            )
                        )
        return contributor

    async def _get_or_create_concept_by_label(
        self, concept_informations: ConceptInformations, new_attempt: bool = False
    ):
        async with async_session() as session:
            async with session.begin_nested():
                concept = await ConceptDAO(session).get_concept_by_label_and_language(
                    label=concept_informations.label,
                    language=concept_informations.language,
                )
                if concept is None:
                    concept = Concept(uri=concept_informations.uri)
                    concept.labels.append(
                        Label(
                            value=concept_informations.label,
                            language=concept_informations.language,
                        )
                    )
                    session.add(concept)
                    try:
                        await session.commit()
                    except IntegrityError as error:
                        # The concept has been created by another process,
                        # during resolution process,
                        # so rollback the current transaction
                        # and get the concept from the database
                        assert new_attempt is False, (
                            f"Unique label {concept_informations.label} "
                            "for concept without uri violation cannot occur twice "
                            f"during concept creation : {error}"
                        )
                        await session.rollback()
                        concept = await self._get_or_create_concept_by_label(
                            concept_informations=concept_informations, new_attempt=True
                        )
        return concept

    @execution_timer
    async def _get_or_create_concept_by_uri(
        self,
        concept_informations: ConceptInformations,
        new_attempt: bool = False,
    ):
        concept = None
        # Look for the concept in the database
        async with async_session() as session:
            async with session.begin_nested():
                # First we resolve the uri of the concept
                ConceptFactory.complete_information(concept_informations)
                concept = await ConceptDAO(session).get_concept_by_uri(
                    concept_informations.uri
                )
                # If the concept is not in the database, try to create it by dereferencing the uri
        if concept is not None:
            return concept
        try:
            concept = await ConceptFactory.solve(concept_informations)
        except DereferencingError as error:
            # If the dereferencing fails, create a concept with the uri and the label
            logger.error(
                "Dereferencing failure for concept "
                f"{concept_informations.uri} with error: {error}"
            )
            concept = Concept(uri=concept_informations.uri)
            if concept_informations.label is not None:
                concept.labels.append(
                    Label(
                        value=concept_informations.label,
                        language=concept_informations.language,
                    )
                )
        async with async_session() as session:
            async with session.begin_nested():
                session.add(concept)
                try:
                    await session.commit()
                except IntegrityError as error:
                    # The concept has been created by another process,
                    # during resolution process,
                    # so rollback the current transaction
                    # and get the concept from the database
                    assert new_attempt is False, (
                        f"Unique uri {concept_informations.uri} violation "
                        "cannot occur twice "
                        f"during concept creation : {error}"
                    )
                    await session.rollback()
                    concept = await self._get_or_create_concept_by_uri(
                        concept_informations=concept_informations, new_attempt=True
                    )
        return concept

    async def _get_or_create_concepts_by_uri(
        self,
        concept_informations: List[ConceptInformations],
    ):
        db_concepts = []
        # get all the concepts from the database in one query
        async with async_session() as session:
            db_concepts = await ConceptDAO(session).get_concepts_by_uri(
                [
                    concept_information.uri
                    for concept_information in concept_informations
                ]
            )
        concepts_dereferencing_coroutines = []
        # for each concept information, check if the concept is in the db_concepts list
        # if not, create a coroutine to dereference the concept
        for concept_information in concept_informations:
            if not any(
                concept.uri == concept_information.uri for concept in db_concepts
            ):
                concepts_dereferencing_coroutines.append(
                    self._get_or_create_concept_by_uri(
                        concept_information, new_attempt=False
                    )
                )
        # wait for all the coroutines to finish
        concepts_dereferencing_results = await asyncio.gather(
            *concepts_dereferencing_coroutines
        )
        # add the dereferenced concepts to the db_concepts list
        db_concepts.extend(concepts_dereferencing_results)
        return db_concepts

    async def _get_or_create_document_type_by_uri(
        self, uri: str, label: str | None, new_attempt: bool = False
    ):
        async with async_session() as session:
            async with session.begin_nested():
                document_type = await DocumentTypeDAO(session).get_document_type_by_uri(
                    uri
                )
                if document_type is None:
                    document_type = DocumentType(uri=uri, label=label)
                    session.add(document_type)
                    try:
                        await session.commit()
                    except IntegrityError as error:
                        # The document type has been created
                        # by another process, during creation process,
                        # so rollback the current transaction
                        # and get the the document type from the database
                        assert new_attempt is False, (
                            f"Unique uri {uri} violation "
                            "cannot occur twice "
                            f"during document type creation : {error}"
                        )
                        await session.rollback()
                        document_type = await self._get_or_create_document_type_by_uri(
                            uri, label, new_attempt=True
                        )
        return document_type

    def _update_contributor_name(self, db_contributor: Contributor, name: str):
        """
        Updates the name of the contributor if it is different from the one in the database
        and stores the old name in the name_variants field

        :param db_contributor:
        :param name: new name received from hal
        :return: None
        """
        if db_contributor.name == name:
            return
        if db_contributor.name not in db_contributor.name_variants:
            # with append method sqlalchemy would not detect the change
            db_contributor.name_variants = db_contributor.name_variants + [
                db_contributor.name
            ]
        db_contributor.name = name

    async def _organizations(
        self, organization_informations: List[OrganizationInformations]
    ) -> AsyncGenerator[Organization, None]:
        # Get all the organizations from the database, or create if they do not exist
        organizations_identifiers_cache = {}
        for organization_information in organization_informations:
            identifier = organization_information.identifier
            assert identifier is not None, "No identifier provided for organization"
            db_organization = organizations_identifiers_cache.get(identifier)
            if db_organization is None:
                db_organization = await self._get_or_create_organization_by_identifier(
                    organization_informations=organization_information
                )
                organizations_identifiers_cache[identifier] = db_organization

            yield db_organization

    async def _get_or_create_organization_by_identifier(
        self,
        organization_informations: OrganizationInformations,
        new_attempt: bool = False,
    ):
        async with async_session() as session:
            async with session.begin_nested():
                organization = await OrganizationDAO(
                    session
                ).get_organization_by_source_identifier(
                    identifier=organization_informations.identifier
                )

                if organization is None:
                    try:
                        organization = await OrganizationFactory.solve(
                            organization_informations
                        )

                        same_organization = await OrganizationDAO(
                            session
                        ).get_organization_by_identifiers(organization.identifiers)
                        if same_organization is not None and len(
                            same_organization.identifiers
                        ) != len(organization.identifiers):
                            organization = merge_organization(
                                same_organization, organization
                            )

                    except DereferencingError:
                        organization = Organization(
                            source=organization_informations.source,
                            source_identifier=organization_informations.identifier,
                            name=organization_informations.name,
                        )
                    session.add(organization)
                    try:
                        await session.commit()
                    except IntegrityError as error:
                        assert new_attempt is False, (
                            f"Unique identifier {organization_informations.identifier} violation "
                            "for organization cannot occur twice "
                            f"during organization creation : {error}"
                        )
                        await session.rollback()
                        organization = (
                            await self._get_or_create_organization_by_identifier(
                                organization_informations=organization_informations,
                                new_attempt=True,
                            )
                        )
                else:
                    await session.refresh(organization)
        return organization

    async def _get_or_create_issue(
        self, issue_informations: IssueInformations, new_attempt: bool = False
    ):
        """
        Try to get an issue by source and source identifier.
        If not found, create it.
        """
        async with async_session() as session:
            async with session.begin_nested():
                issue = await IssueDAO(
                    session
                ).get_issue_by_source_and_source_identifier(
                    source=issue_informations.source,
                    source_identifier=issue_informations.source_identifier,
                )

                if issue is None:
                    issue = Issue(
                        source=issue_informations.source,
                        source_identifier=issue_informations.source_identifier,
                        journal=issue_informations.journal,
                        journal_id=issue_informations.journal.id,
                        titles=issue_informations.titles,
                        volume=issue_informations.volume,
                        number=issue_informations.number,
                        date=issue_informations.date,
                        rights=issue_informations.rights,
                    )
                    session.add(issue)
                    try:
                        await session.commit()
                    except IntegrityError as error:
                        assert new_attempt is False, (
                            f"Unique source and source identifier violation "
                            "for issue cannot occur twice "
                            f"during issue creation : {error}"
                        )
                        await session.rollback()
                        issue = await self._get_or_create_issue(
                            issue_informations=issue_informations, new_attempt=True
                        )
                else:
                    # journal is not set as lazy=raise
                    issue.journal = issue_informations.journal
        return issue

    async def _get_or_create_journal(
        self, journal_informations: JournalInformations, new_attempt: bool = False
    ) -> Journal:
        """
        Try to get a journal by source and issn/eissn.
        If not found, try to get by source and source_identifier.
        If not found, create it.
        """
        async with async_session() as session:
            async with session.begin_nested():
                journal = await JournalDAO(
                    session
                ).get_journal_by_source_issn_or_eissn_or_issn_l(
                    source=journal_informations.source,
                    issn=journal_informations.issn,
                    eissn=journal_informations.eissn,
                    issn_l=journal_informations.issn_l,
                )
                if journal is None:
                    journal = await JournalDAO(
                        session
                    ).get_journal_by_source_identifier_and_source(
                        source=journal_informations.source,
                        source_identifier=journal_informations.source_identifier,
                    )
                if journal is None:
                    journal = Journal(
                        source=journal_informations.source,
                        source_identifier=journal_informations.source_identifier,
                        eissn=journal_informations.eissn,
                        issn=journal_informations.issn,
                        issn_l=journal_informations.issn_l,
                        publisher=journal_informations.publisher,
                        titles=journal_informations.titles,
                    )
                    session.add(journal)
                    try:
                        await session.commit()
                    except DBAPIError as error:
                        assert new_attempt is False, (
                            f"Unique source and source identifier violation "
                            "for journal cannot occur twice "
                            f"during journal creation : {error}"
                        )
                        await session.rollback()
                        journal = await self._get_or_create_journal(
                            journal_informations=journal_informations, new_attempt=True
                        )
        return journal

    async def _get_or_create_book(
        self, book_informations: BookInformations, new_attempt: bool = False
    ) -> Book:
        """
        Try to get a book by isbn10/isbn13.
        If not found, try to get by title.
        If not found, create it.
        """
        async with async_session() as session:
            async with session.begin_nested():
                book = await BookDAO(session).get_books_by_isbn(
                    source=book_informations.source,
                    isbn10=book_informations.isbn10,
                    isbn13=book_informations.isbn13,
                )
                if book is None:
                    book = await BookDAO(session).get_books_by_title(
                        source=book_informations.source, title=book_informations.title
                    )
                if book is None:
                    book = Book(
                        source=book_informations.source,
                        title=book_informations.title,
                        isbn10=book_informations.isbn10,
                        isbn13=book_informations.isbn13,
                        publisher=book_informations.publisher,
                    )
                    session.add(book)
                    try:
                        await session.commit()
                    except DBAPIError as error:
                        assert new_attempt is False, (
                            f"Unique isbn10 and isbn13 violation"
                            "for book cannot occur twice "
                            f"during book creation : {error}"
                        )
                        await session.rollback()
                        book = await self._get_or_create_book(
                            book_informations=book_informations, new_attempt=True
                        )
                else:
                    book = self._update_book(book, book_informations)

        return book

    def _update_book(self, book: Book, book_informations: BookInformations):
        """
        Update the book with the new informations
        """
        if (book.title != book_informations.title) and (
            book_informations.title not in book.title_variants
        ):
            book.title_variants.append(book.title)
        return book
