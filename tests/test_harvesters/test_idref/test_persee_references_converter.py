import datetime

import pytest
from semver import VersionInfo

from app.harvesters.idref.persee_references_converter import PerseeReferencesConverter


@pytest.mark.asyncio
async def test_persee_convert_for_rdf_result(persee_rdf_result_for_doc):
    """
    GIVEN a PerseeReferencesConverter instance and a Persee RDF result for a document
    WHEN the convert method is called
    THEN it should return a Reference instance with the expected values

    :param: a Persee RDF result for a document
    :return: None
    """
    converter_under_tests = PerseeReferencesConverter()

    expected_source_identifier = (
        "http://data.persee.fr/doc/hista_0992-2059_1998_num_42_1_2826#Web"
    )
    expected_abstract_en = (
        "designed for university education buildings dates"
        " back to the end of the 18th century, but the golden"
    )
    expected_abstract_language = "en"
    expected_title = (
        "Le décor peint des établissements d’enseignement"
        " supérieur à Paris. De la conception à la réception"
    )
    expected_document_type = "Document"
    expected_auth_name = "Christian Hottin"
    expected_page = "103-113"
    expected_issue = "1"
    expected_volume = "18"
    expected_journal_title = "Cahiers du Centre Gustave Glotz, 18, 2007."
    expected_publisher = "Paris : Centre Gustave Glotz"
    expected_raw_issued_date = "1998-01-01"
    expected_issued_date = datetime.date(1998, 1, 1)
    expected_created_date = datetime.date(2021, 6, 23)

    expected_subjects = [
        "university",
        "amphitheater",
        "artistic heritage",
        "History painting",
        "commissioned works of art",
        "mural painting",
        "group portrait",
        "Paris, Sorbonne, Law School, Faculty of Medicine, Faculty of Pharmacy.",
        "architectural decor, France, 18th-20th centuries",
    ]

    test_reference = converter_under_tests.build(
        raw_data=persee_rdf_result_for_doc, harvester_version=VersionInfo.parse("0.0.0")
    )
    assert test_reference.source_identifier == expected_source_identifier
    await converter_under_tests.convert(
        raw_data=persee_rdf_result_for_doc, new_ref=test_reference
    )
    assert expected_title == test_reference.titles[0].value
    assert expected_abstract_en in test_reference.abstracts[0].value
    assert expected_abstract_language == test_reference.abstracts[0].language
    assert any(
        document_type.label == expected_document_type
        for document_type in test_reference.document_type
    )
    assert len(test_reference.contributions) == 1
    assert expected_auth_name == test_reference.contributions[0].contributor.name.value
    assert test_reference.identifiers[0].value == expected_source_identifier
    assert test_reference.page == expected_page
    assert expected_issue == test_reference.issue.number
    assert expected_volume == test_reference.issue.volume
    assert expected_journal_title in test_reference.issue.journal.titles
    assert test_reference.issue.journal.publisher == expected_publisher
    assert test_reference.raw_issued == expected_raw_issued_date
    assert test_reference.issued == expected_issued_date
    assert test_reference.created == expected_created_date
    assert expected_publisher == test_reference.issue.journal.publisher

    test_subjects = []
    for subject in test_reference.subjects:
        for label in subject.labels:
            test_subjects.append(label.value)

    assert test_subjects == expected_subjects


@pytest.mark.parametrize(
    "fixture, tested_field, expected_output",
    [
        (
            "persee_rdf_result_for_doc_with_invalid_dateofpublication",
            "created",
            "Could not parse date",
        ),
        (
            "persee_rdf_result_for_doc_with_invalid_dateofprintpublication",
            "issued",
            "Could not parse date",
        ),
    ],
)
async def test_convert_with_invalid_date_format(
    fixture, tested_field, expected_output, caplog, request
):
    """
    GIVEN a PerseeReferencesConverter instance and a
    Persee RDF result for a document with invalid date format
    WHEN the convert method is called
    THEN it should raise a log error and date should be None
    """

    converter_under_tests = PerseeReferencesConverter()

    fixture = request.getfixturevalue(fixture)

    test_reference = converter_under_tests.build(
        raw_data=fixture, harvester_version=VersionInfo.parse("0.0.0")
    )

    await converter_under_tests.convert(raw_data=fixture, new_ref=test_reference)

    assert getattr(test_reference, tested_field) is None
    assert "Persee reference converter cannot create" in caplog.text
    assert expected_output in caplog.text
