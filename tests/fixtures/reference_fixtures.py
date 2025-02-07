import isodate
import pytest_asyncio

from app.db.models.concept import Concept as DbConcept
from app.db.models.issue import Issue
from app.db.models.journal import Journal
from app.db.models.label import Label
from app.db.models.reference import Reference as DbReference
from app.db.models.subtitle import Subtitle
from app.db.models.title import Title


@pytest_asyncio.fixture(name="reference_db_model")
async def fixture_reference_db_model() -> DbReference:
    """
    Create a reference db model
    :return: reference db model
    """
    reference = DbReference(
        source_identifier="123456789",
        harvester="hal",
        hash="hash1",
        version=0,
        titles=[Title(value="title", language="fr")],
        subtitles=[Subtitle(value="subtitle", language="fr")],
        raw_issued="2017",
        issued=isodate.parse_datetime("2017-01-01T00:00:00"),
        created=isodate.parse_datetime("2018-02-02T10:00:00"),
    )
    reference.subjects.append(
        DbConcept(
            uri="http://uri",
            labels=[Label(value="label", language="fr")],
        )
    )
    return reference


@pytest_asyncio.fixture(name="reference_version_0_without_details_db_model")
async def fixture_reference_version_0_without_details_db_model() -> DbReference:
    """
    Create a reference db model without details
    :return: reference db model
    """
    return DbReference(
        source_identifier="123456789",
        harvester="openalex",
        hash="hash1",
        version=0,
        titles=[Title(value="Publication with poor description", language="en")],
        subtitles=[],
        issued=None,
        created=None,
    )


@pytest_asyncio.fixture(name="reference_version_1_with_details_db_model")
async def fixture_reference_version_1_with_details_db_model() -> DbReference:
    """
    Create a reference db model with details
    :return: reference db model
    """
    reference = DbReference(
        source_identifier="123456789",
        harvester="openalex",
        hash="hash1",
        version=1,
        titles=[Title(value="Publication with rich description", language="en")],
        subtitles=[Subtitle(value="subtitle", language="en")],
        issued=isodate.parse_datetime("2017-01-01T00:00:00"),
        created=isodate.parse_datetime("2018-02-02T10:00:00"),
        issue=Issue(
            source="openalex",
            source_identifier="https://openalex.org/s41586-021-03666-1",
            volume="50",
            number=["08"],
            rights="CC BY 4.0",
            date="2021",
            journal=Journal(
                source="openalex",
                source_identifier="https://openalex.org/S2764375719",
                issn=["0009-4978", "1523-8253", "1943-5975"],
                eissn=[],
                issn_l="0009-4978",
                publisher="Association publishers",
                titles=["Scientific journal"],
            ),
        ),
    )

    reference.subjects.append(
        DbConcept(
            uri="http://uri",
            labels=[Label(value="label", language="fr")],
        )
    )
    return reference
