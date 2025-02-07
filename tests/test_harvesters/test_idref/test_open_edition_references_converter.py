import datetime

import pytest
from semver import VersionInfo

from app.harvesters.idref.open_edition_references_converter import (
    OpenEditionReferencesConverter,
)


@pytest.mark.asyncio
async def test_open_edition_convert_for_rfd_result(
    open_edition_xml_result_for_doc,
):
    """
    GIVEN a OpenEditionReferencesConverter instance and a Open Edition XML result for a document
    WHEN the convert method is called
    THEN it should return a Reference instance with the expected values

    :param: open_edition_xml_result_for_doc: a Open Edition RDF result for a document
    :return: None
    """
    converter_under_tests = OpenEditionReferencesConverter()
    test_reference = converter_under_tests.build(
        raw_data=open_edition_xml_result_for_doc,
        harvester_version=VersionInfo.parse("0.0.0"),
    )
    await converter_under_tests.convert(
        raw_data=open_edition_xml_result_for_doc, new_ref=test_reference
    )
    expected_french_title = "Les émeutes entre hindous et musulmans (partie 2)"
    expected_french_abstract_beginning = (
        "Si le caractère très ancien et les facteurs religieux des émeutes"
    )
    expected_reference_identifier = [
        "https://journals.openedition.org/conflits/756",
        "10.4000/conflits.756",
    ]
    expected_publisher = "L’Harmattan"
    expected_journal_title = "Cultures & conflits"
    expected_issue_rights = "https://creativecommons.org/licenses/by-nc-nd/4.0/"
    expected_raw_issued_date = "2003-01-02T00:00:00Z"
    expected_issued_date = datetime.datetime(2003, 1, 2, 0, 0)
    expected_created_date = datetime.date(1992, 1, 1)

    assert test_reference.source_identifier == str(
        open_edition_xml_result_for_doc.source_identifier
    )
    assert len(test_reference.titles) == 1
    assert expected_french_title in [title.value for title in test_reference.titles]
    assert any(
        abstract.value.startswith(expected_french_abstract_beginning)
        for abstract in test_reference.abstracts
    )
    assert any(
        identifier.value in expected_reference_identifier
        for identifier in test_reference.identifiers
    )
    assert test_reference.document_type[0].label == "Article"
    assert expected_publisher == test_reference.issue.journal.publisher
    assert expected_journal_title in test_reference.issue.journal.titles
    assert expected_issue_rights == test_reference.issue.rights
    assert test_reference.raw_issued == expected_raw_issued_date
    assert test_reference.issued == expected_issued_date
    assert test_reference.created == expected_created_date


@pytest.mark.parametrize(
    "fixture, reference_field, expected_output",
    [
        ("open_edition_xml_invalid_created_format", "created", "Could not parse date"),
        ("open_edition_xml_invalid_issued_format", "issued", "Could not parse date"),
    ],
)
async def test_convert_with_invalid_date_format(
    fixture, expected_output, reference_field, caplog, request
):
    """
    Test that the ScopusReferencesConverter will handle an invalid date format gracefully
    """
    converter_under_tests = OpenEditionReferencesConverter()

    fixture = request.getfixturevalue(fixture)

    test_reference = converter_under_tests.build(
        raw_data=fixture,
        harvester_version=VersionInfo.parse("0.0.0"),
    )

    await converter_under_tests.convert(raw_data=fixture, new_ref=test_reference)

    assert getattr(test_reference, reference_field) is None
    assert "OpenEdition reference converter cannot create" in caplog.text
    assert expected_output in caplog.text
