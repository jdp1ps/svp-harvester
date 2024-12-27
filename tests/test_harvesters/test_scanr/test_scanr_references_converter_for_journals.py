import pytest
from semver import VersionInfo

from app.harvesters.exceptions.unexpected_format_exception import (
    UnexpectedFormatException,
)
from app.harvesters.json_harvester_raw_result import JsonHarvesterRawResult
from app.harvesters.scanr.scanr_references_converter import ScanrReferencesConverter


@pytest.fixture(name="scanr_publication_doc_with_journal_without_title")
def fixture_scanr_publication_doc_with_journal_without_title(
    scanr_publication_doc_with_journal_without_title,
):
    """Return the list of dictionaries references from scanr response"""
    return scanr_publication_doc_with_journal_without_title["hits"]["hits"]


@pytest.fixture(name="scanr_publication_doc_with_journal_with_title")
def fixture_scanr_publication_doc_with_journal_with_title(
    scanr_publication_doc_with_journal_with_title,
):
    """Return the list of dictionaries references from scanr response"""
    return scanr_publication_doc_with_journal_with_title["hits"]["hits"]


async def test_convert_publication_with_journal_without_title(
    scanr_publication_doc_with_journal_without_title,
):
    converter_under_tests = ScanrReferencesConverter()

    for doc in scanr_publication_doc_with_journal_without_title:
        result = JsonHarvesterRawResult(
            source_identifier=doc.get("_id"), payload=doc, formatter_name="SCANR"
        )

        test_reference = converter_under_tests.build(
            raw_data=result, harvester_version=VersionInfo.parse("0.0.0")
        )
        await converter_under_tests.convert(raw_data=result, new_ref=test_reference)
        journal = test_reference.issue.journal
        assert "Missing ScanR journal title" in journal.titles


async def test_convert_publication_with_journal_with_title(
    scanr_publication_doc_with_journal_with_title,
):
    converter_under_tests = ScanrReferencesConverter()

    expected_title = "Bulletin de la Société préhistorique française"

    for doc in scanr_publication_doc_with_journal_with_title:
        result = JsonHarvesterRawResult(
            source_identifier=doc.get("_id"), payload=doc, formatter_name="SCANR"
        )

        test_reference = converter_under_tests.build(
            raw_data=result, harvester_version=VersionInfo.parse("0.0.0")
        )
        await converter_under_tests.convert(raw_data=result, new_ref=test_reference)

        journal = test_reference.issue.journal
        assert expected_title in journal.titles
