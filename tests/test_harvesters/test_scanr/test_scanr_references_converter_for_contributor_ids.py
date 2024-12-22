import pytest
from semver import VersionInfo

from app.db.daos.contributor_dao import ContributorDAO
from app.db.session import async_session
from app.harvesters.json_harvester_raw_result import JsonHarvesterRawResult
from app.harvesters.scanr.scanr_references_converter import ScanrReferencesConverter


@pytest.fixture(name="scanr_publication_doc_with_journal_with_title")
def fixture_scanr_publication_doc_with_journal_with_title(
    scanr_publication_doc_with_journal_with_title,
):
    """Return the list of dictionaries references from scanr response"""
    return scanr_publication_doc_with_journal_with_title["hits"]["hits"]


async def test_convert_publication_with_contributor_ids(
    scanr_publication_doc_with_journal_with_title,
):
    converter_under_tests = ScanrReferencesConverter()

    doc = scanr_publication_doc_with_journal_with_title[0]
    result = JsonHarvesterRawResult(
        source_identifier=doc.get("_id"), payload=doc, formatter_name="SCANR"
    )

    test_reference = converter_under_tests.build(
        raw_data=result, harvester_version=VersionInfo.parse("0.0.0")
    )
    await converter_under_tests.convert(raw_data=result, new_ref=test_reference)

    # take contribution of rank 1
    contribution = next(c for c in test_reference.contributions if c.rank == 1)
    contributor_id = contribution.contributor.id
    assert contributor_id is not None
    assert isinstance(contributor_id, int)
    async with async_session() as session:
        async with session.begin_nested():
            contributor = await ContributorDAO(session).get_by_id(contributor_id)
            assert contributor is not None
            assert len(contributor.identifiers) == 3
            assert any(
                [
                    identifier.type == "orcid"
                    and identifier.value == "https://orcid.org/0000-0002-9981-9598"
                    for identifier in contributor.identifiers
                ]
            )
            assert any(
                [
                    identifier.type == "idref" and identifier.value == "028738497"
                    for identifier in contributor.identifiers
                ]
            )
            assert any(
                [
                    identifier.type == "idhal" and identifier.value == "valentine-roux"
                    for identifier in contributor.identifiers
                ]
            )
