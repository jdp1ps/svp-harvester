import datetime

import pytest
from semver import VersionInfo

from app.db.daos.contributor_dao import ContributorDAO
from app.db.models.contribution import Contribution
from app.db.session import async_session
from app.harvesters.scopus.scopus_client import ScopusClient
from app.harvesters.scopus.scopus_references_converter import ScopusReferencesConverter
from app.harvesters.xml_harvester_raw_result import XMLHarvesterRawResult


@pytest.mark.asyncio
async def test_convert(scopus_xml_raw_result_for_doc: XMLHarvesterRawResult):
    """Test that the converter will return normalised references"""
    converter_under_test = ScopusReferencesConverter()

    test_reference = converter_under_test.build(
        raw_data=scopus_xml_raw_result_for_doc,
        harvester_version=VersionInfo.parse("0.0.0"),
    )

    await converter_under_test.convert(
        raw_data=scopus_xml_raw_result_for_doc, new_ref=test_reference
    )

    expected_title = (
        "Is musculoskeletal pain associated with increased muscle stiffness?"
    )

    expected_abstract = "Introduction and Aims: Approximately 21% of the world's"
    expected_identifier = ["10.1111/cpf.12870", "38155545"]
    expected_document_type = "Review"
    expected_concepts = [
        "imaging methods",
        "muscle",
        "musculoskeletal pain",
        "shear wave elastography",
        "stiffness",
    ]
    expected_authors = [
        "Haueise A.",
        "Le Sant G.",
        "Eisele-Metzger A.",
        "Dieterich A.V.",
    ]
    expected_affiliation = ["Hochschule Furtwangen", "CHU de Nantes"]

    expected_page = "132-134"
    expected_issn = ["1111-2222"]
    expected_eissn = ["3333-4444"]
    expected_journal_title = "Clinical Physiology and Functional Imaging"
    expected_volume_issue = "12"
    expected_number_issue = "1"
    expected_role = Contribution.get_url("AUT")
    expected_issued = datetime.date(2024, 1, 1)

    assert test_reference.titles[0].value == expected_title
    assert test_reference.abstracts[0].value == expected_abstract
    for identifier in test_reference.identifiers:
        assert identifier.value in expected_identifier
    assert test_reference.document_type[0].label == expected_document_type
    for concept in test_reference.subjects:
        for label in concept.labels:
            assert label.value in expected_concepts
    for contribution in test_reference.contributions:
        assert contribution.contributor.name in expected_authors
        assert contribution.role == expected_role
        for affiliation in contribution.affiliations:
            assert affiliation.name in expected_affiliation
    assert test_reference.page == expected_page
    assert test_reference.issue.journal.issn == expected_issn
    assert test_reference.issue.journal.eissn == expected_eissn
    assert expected_journal_title in test_reference.issue.journal.titles
    assert test_reference.issue.volume == expected_volume_issue
    assert expected_number_issue in test_reference.issue.number
    assert test_reference.issued == expected_issued

    contribution = test_reference.contributions[0]
    contributor_id = contribution.contributor.id
    assert contributor_id is not None
    assert isinstance(contributor_id, int)
    async with async_session() as session:
        async with session.begin_nested():
            contributor = await ContributorDAO(session).get_by_id(contributor_id)
            assert contributor is not None
            assert len(contributor.identifiers) == 2
            assert any(
                [
                    identifier.type == "orcid"
                    and identifier.value == "https://orcid.org/0000-0002-5201-3968"
                    for identifier in contributor.identifiers
                ]
            )
            assert any(
                [
                    identifier.type == "scopus" and identifier.value == "57539748900"
                    for identifier in contributor.identifiers
                ]
            )


@pytest.mark.asyncio
async def test_convert_book(scopus_xml_raw_result_for_doc_book):
    """Test that the converter will return normalised references with book info"""

    converter_under_test = ScopusReferencesConverter()

    test_reference = converter_under_test.build(
        raw_data=scopus_xml_raw_result_for_doc_book,
        harvester_version=VersionInfo.parse("0.0.0"),
    )

    await converter_under_test.convert(
        raw_data=scopus_xml_raw_result_for_doc_book, new_ref=test_reference
    )

    expected_title_book = "Sustainability Accounting and Accountability"
    expected_isbn10 = "0203815289"
    expected_isbn13 = "9780203815281"

    assert test_reference.book.title == expected_title_book
    assert test_reference.book.isbn10 == expected_isbn10
    assert test_reference.book.isbn13 == expected_isbn13


@pytest.mark.asyncio
async def test_convert_with_invalid_date_format(scopus_xml_raw_result_for_doc, caplog):
    """
    Test that the ScopusReferencesConverter will handle an invalid date format gracefully
    """
    converter_under_tests = ScopusReferencesConverter()

    # Simulate invalid date format
    existing_cover_date = scopus_xml_raw_result_for_doc.payload.find(
        "prism:coverDate", ScopusClient.NAMESPACE
    )
    if existing_cover_date is not None:
        existing_cover_date.text = "invalid-date"

    test_reference = converter_under_tests.build(
        raw_data=scopus_xml_raw_result_for_doc,
        harvester_version=VersionInfo.parse("0.0.0"),
    )

    await converter_under_tests.convert(
        raw_data=scopus_xml_raw_result_for_doc, new_ref=test_reference
    )

    assert test_reference.issued is None
    assert (
        "Scopus reference converter cannot create issued date from coverDate"
        in caplog.text
    )
