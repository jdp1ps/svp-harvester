from typing import List

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db.abstract_dao import AbstractDAO
from app.db.models.contributor import Contributor
from app.db.models.external_person_identifier import ExternalPersonIdentifier


class ContributorDAO(AbstractDAO):
    """
    Data access object for contributors
    """

    async def get_by_id(self, contributor_id: int) -> Contributor:
        """
        Get a contributor by its id
        :param contributor_id: id of the contributor
        :return: contributor
        """
        return await self.db_session.get(Contributor, contributor_id)

    async def get_by_source_and_name(self, source: str, name: str) -> Contributor:
        """
        Get a contributor by source and name field
        :param source: source of the contributor ("hal", "idref"...)
        :param name: name of the contributor
        :return: contributor
        """
        stmt = (
            select(Contributor)
            .options(joinedload(Contributor.identifiers))
            .where(Contributor.source == source)
            .where(Contributor.name == name)
            # where source identifier is null
            .where(Contributor.source_identifier.is_(None))
        )
        return (await self.db_session.execute(stmt)).unique().scalars().one_or_none()

    async def get_by_source_and_identifier(
        self, source: str, source_identifier: str
    ) -> Contributor:
        """
        Get a contributor by source and source identifier
        :param source: source of the contributor ("hal", "idref"...)
        :param source_identifier: identifier of the contributor in the source
        :return: contributor
        """
        stmt = (
            select(Contributor)
            .options(joinedload(Contributor.identifiers))
            .where(Contributor.source == source)
            .where(Contributor.source_identifier == source_identifier)
        )
        return (await self.db_session.execute(stmt)).unique().scalars().one_or_none()

    async def update_external_identifiers(
        self, contributor_id: int, ext_identifiers: List[dict[str, str]] = []
    ) -> List[ExternalPersonIdentifier]:
        """
        Update external identifiers of a contributor
        :param contributor: contributor to update
        :param ext_identifiers: list of external identifiers
        :return: None
        """
        valid_types = self._get_valid_external_identifier_types()
        contributor = await self.get_by_id(contributor_id)

        ext_identifiers = [
            identifier
            for identifier in ext_identifiers
            if identifier["type"] in valid_types
        ]

        existing_identifiers = {
            (id.type, id.value): id for id in contributor.identifiers
        }

        new_identifiers = {
            (identifier["type"], identifier["value"]) for identifier in ext_identifiers
        }

        identifiers_to_remove = set(existing_identifiers) - new_identifiers

        identifiers_to_add = new_identifiers - set(existing_identifiers)

        for identifier_type, identifier_value in identifiers_to_remove:
            identifier = existing_identifiers[(identifier_type, identifier_value)]
            await self.db_session.delete(identifier)

        for identifier_type, identifier_value in identifiers_to_add:
            new_identifier = ExternalPersonIdentifier(
                type=identifier_type,
                value=identifier_value,
                source=contributor.source,
                contributor_id=contributor.id,
            )
            self.db_session.add(new_identifier)

    def _get_valid_external_identifier_types(self):
        valid_types = {
            identifier.value for identifier in ExternalPersonIdentifier.IdentifierType
        }
        return valid_types
