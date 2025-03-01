import datetime
from typing import List, Tuple

from sqlalchemy import and_, func, select
from sqlalchemy.orm import joinedload

from app.db.abstract_dao import AbstractDAO
from app.db.daos.entity_dao import EntityDAO
from app.db.daos.harvesting_dao import HarvestingDAO
from app.db.models.issue import Issue
from app.db.models.references_document_type import references_document_type_table
from app.db.models.document_type import DocumentType
from app.db.models.entity import Entity
from app.db.models.harvesting import Harvesting
from app.db.models.identifier import Identifier
from app.db.models.reference_event import ReferenceEvent
from app.db.models.retrieval import Retrieval
from app.db.models.reference import Reference
from app.models.people import Person
from app.utilities.string_utilities import split_string


# pylint: disable=not-callable, duplicate-code
class RetrievalDAO(AbstractDAO):
    """
    Data access object for Retrieval
    """

    async def create_retrieval(
        self, entity: Entity, event_types: List[ReferenceEvent.Type] = None
    ) -> Retrieval:
        """
        Create a retrieval for an entity we want to fetch references for

        :param entity: the entity we want to fetch references for
        :return: the created retrieval
        """
        retrieval = Retrieval()
        retrieval.entity = entity
        retrieval.event_types = event_types or []
        self.db_session.add(retrieval)
        return retrieval

    async def get_retrieval_by_id(self, retrieval_id: int) -> Retrieval | None:
        """
        Get a retrieval by its id

        :param retrieval_id: id of the retrieval
        :return: the retrieval or None if not found
        """
        return await self.db_session.get(Retrieval, retrieval_id)

    async def get_complete_retrieval_by_id(self, retrieval_id: int) -> Retrieval | None:
        """
        Get a retrieval by its id with all its references

        :param retrieval_id: id of the retrieval
        :return: the retrieval or None if not found
        """
        stmt = (
            select(Retrieval)
            .options(
                joinedload(Retrieval.harvestings)
                .joinedload(Harvesting.reference_events)
                .options(
                    joinedload(ReferenceEvent.reference).joinedload(
                        Reference.contributions, innerjoin=False
                    )
                )
                .options(
                    joinedload(ReferenceEvent.reference).joinedload(
                        Reference.abstracts, innerjoin=False
                    )
                )
                .options(
                    joinedload(ReferenceEvent.reference).joinedload(
                        Reference.subjects, innerjoin=False
                    )
                )
                .options(
                    joinedload(ReferenceEvent.reference)
                    .joinedload(Reference.issue, innerjoin=False)
                    .options(joinedload(Issue.journal, innerjoin=False))
                )
            )
            .where(Retrieval.id == retrieval_id)
        )
        return (await self.db_session.execute(stmt)).unique().scalar_one_or_none()

    async def get_retrieval_display_info_by_id(
        self, retrieval_id: int
    ) -> Retrieval | None:
        """
        Get minimal information about a retrieval by its id

        :param retrieval_id: id of the retrieval
        :return: the retrieval or None if not found
        """
        stmt = (
            select(Retrieval)
            .options(
                joinedload(Retrieval.harvestings)
                .joinedload(Harvesting.reference_events)
                .options(
                    joinedload(ReferenceEvent.reference).noload(Reference.contributions)
                )
                .options(
                    joinedload(ReferenceEvent.reference).noload(Reference.identifiers)
                )
                .options(
                    joinedload(ReferenceEvent.reference).noload(Reference.document_type)
                )
            )
            .where(Retrieval.id == retrieval_id)
        )
        return (await self.db_session.execute(stmt)).unique().scalar_one_or_none()

    async def get_retrievals_summary(
        self,
        filter_harvester: dict[List],
        date_interval: Tuple[datetime.date, datetime.date],
        entity: Person,
    ) -> List[Retrieval]:
        """
        Get retrieval history for a given entity
        :param filter_harvester: filter for the harvester (event_types, nullify, harvester)
        :param date_interval: date interval to fetch
        :param entity: entity to search

        :return: Retrieval history
        """
        date_start, date_end = date_interval

        harvesting_event_count = HarvestingDAO(
            self.db_session
        ).harvesting_event_count_subquery(
            filter_harvester["event_types"], filter_harvester["nullify"]
        )

        if entity:
            entity_id = EntityDAO(self.db_session).entity_filter_subquery(entity)
        else:
            entity_id = EntityDAO(self.db_session).get_all_entities_subquery()

        stmt = (
            select(
                Retrieval.id,
                Retrieval.timestamp,
                (entity_id.c.name).label("entity_name"),
                (
                    func.array_agg(func.distinct(Identifier.type, Identifier.value))
                ).label("identifier_type"),
                (func.count(ReferenceEvent.id.distinct())).label("event_count"),
                (func.array_agg(DocumentType.label.distinct())).label("document_type"),
                (
                    func.array_agg(
                        func.distinct(
                            Harvesting.harvester,
                            Harvesting.state,
                            harvesting_event_count.c.type_event,
                            harvesting_event_count.c.count,
                        )
                    )
                ).label("harvesting_state"),
            )
            .join(Harvesting, onclause=Retrieval.id == Harvesting.retrieval_id)
            .join(
                harvesting_event_count,
                onclause=Harvesting.id == harvesting_event_count.c.id,
            )
            .join(entity_id, onclause=Retrieval.entity_id == entity_id.c.id)
            .join(Identifier, onclause=entity_id.c.id == Identifier.entity_id)
            .join(
                ReferenceEvent, onclause=Harvesting.id == ReferenceEvent.harvesting_id
            )
            .outerjoin(Reference, onclause=ReferenceEvent.reference_id == Reference.id)
            .outerjoin(
                references_document_type_table,
                onclause=Reference.id == references_document_type_table.c.reference_id,
            )
            .outerjoin(
                DocumentType,
                onclause=DocumentType.id
                == references_document_type_table.c.document_type_id,
            )
            .where(
                func.lower(Reference.harvester).in_(
                    [func.lower(h) for h in filter_harvester["harvester"]]
                )
            )
            .order_by(Retrieval.timestamp.desc())
            .group_by(Retrieval.id, entity_id.c.name)
        )

        if entity and entity.name:
            names = split_string(entity.name)
            stmt = stmt.filter(
                and_(*[entity_id.c.name.like(f"%{name}%") for name in names])
            )
        if date_start:
            stmt = stmt.where(Harvesting.timestamp >= date_start)
        if date_end:
            stmt = stmt.where(Harvesting.timestamp <= date_end)
        return await self.db_session.execute(stmt)
