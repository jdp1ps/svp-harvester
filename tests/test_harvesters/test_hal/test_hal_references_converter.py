import datetime

import pytest
from semver import VersionInfo

from app.db.models.contribution import Contribution
from app.harvesters.hal.hal_references_converter import HalReferencesConverter
from app.harvesters.json_harvester_raw_result import JsonHarvesterRawResult


@pytest.fixture(name="hal_api_cleaned_response")
def fixture_hal_api_cleaned_response(hal_api_docs_for_researcher):
    """Return the list of dictionaries references from hal response"""
    return hal_api_docs_for_researcher["response"]["docs"]


@pytest.fixture(name="hal_api_response_with_uris")
def fixture_hal_api_response_with_uris(hal_api_docs_for_researcher_with_uris):
    """Return the list of dictionaries references from hal response"""
    return hal_api_docs_for_researcher_with_uris["response"]["docs"]


# for hal_api_docs_with_inconsistent_structured_names
@pytest.fixture(name="hal_api_docs_with_inconsistent_structured_names")
def fixture_hal_api_response_with_inconsistent_structured_names(
    hal_api_docs_with_inconsistent_structured_names,
):
    """Return the list of dictionaries references from hal response"""
    return hal_api_docs_with_inconsistent_structured_names["response"]["docs"]


async def test_convert(hal_api_cleaned_response):  # pylint: disable=too-many-locals
    """Test that the converter will return normalised references"""
    converter_under_tests = HalReferencesConverter()

    expected_titles = [
        "Where does « Axial breakthrough » take place? "
        "In the past, or in present narratives of the past?"
    ]
    expected_subjects = [
        "Antiquity",
        "Historiography",
        "Greek city",
        "Vernant",
        "Narration of the past",
    ]
    expected_subtitles = ["test_placeholder_subtitle"]
    expected_docid = "1387023"
    expected_abstracts = ["This article focuses on Vernant..."]
    expected_contributors_number = 1
    expected_contributor_role = Contribution.get_url("AUT")
    expected_contributor_name = "Violaine Sebillotte Cuchet"
    expected_contributor_first_name = "Violaine"
    expected_contributor_last_name = "Sebillotte Cuchet"
    expected_contributor_source = "hal"
    expected_contributor_source_identifier = "10227"
    expected_references_identifier_types = ["hal", "doi"]
    expected_references_identifier_values = ["halshs-01387023", "doi/1234"]
    expected_issued_date = datetime.datetime(2016, 1, 1, 0, 0)
    expected_created_date = datetime.datetime(2016, 1, 1, 0, 0)
    for doc in hal_api_cleaned_response:
        result = JsonHarvesterRawResult(
            source_identifier=doc["docid"], payload=doc, formatter_name="HAL"
        )

        test_reference = converter_under_tests.build(
            raw_data=result, harvester_version=VersionInfo.parse("0.0.0")
        )
        assert test_reference.source_identifier == expected_docid
        await converter_under_tests.convert(raw_data=result, new_ref=test_reference)

        test_titles = [title.value for title in test_reference.titles]
        test_subtitles = [subtitles.value for subtitles in test_reference.subtitles]
        test_abstracts = [abstract.value for abstract in test_reference.abstracts]
        test_subjects = []
        for concept in test_reference.subjects:
            for label in concept.labels:
                test_subjects.append(label.value)

        assert test_titles == expected_titles
        assert test_subjects == expected_subjects
        assert test_subtitles == expected_subtitles
        assert test_abstracts == expected_abstracts
        assert test_reference.issued == expected_issued_date
        assert test_reference.created == expected_created_date
        assert len(test_reference.contributions) == expected_contributors_number
        assert test_reference.contributions[0].role == expected_contributor_role
        assert (
            test_reference.contributions[0].contributor.name
            == expected_contributor_name
        )
        assert (
            test_reference.contributions[0].contributor.first_name
            == expected_contributor_first_name
        )
        assert (
            test_reference.contributions[0].contributor.last_name
            == expected_contributor_last_name
        )
        assert (
            test_reference.contributions[0].contributor.source
            == expected_contributor_source
        )
        assert (
            test_reference.contributions[0].contributor.source_identifier
            == expected_contributor_source_identifier
        )
        for type_, value in zip(
            expected_references_identifier_types, expected_references_identifier_values
        ):
            assert any(
                identifier.type == type_ and identifier.value == value
                for identifier in test_reference.identifiers
            )


async def test_convert_response_with_inconsistent_structured_names(
    hal_api_docs_with_inconsistent_structured_names, caplog
):
    """
    Test that the converter will raise an exception when the number of names in structuredNames
     does not match the number of contributors
    """
    converter_under_tests = HalReferencesConverter()
    for doc in hal_api_docs_with_inconsistent_structured_names:
        result = JsonHarvesterRawResult(
            source_identifier=doc["docid"], payload=doc, formatter_name="HAL"
        )
        reference = converter_under_tests.build(
            raw_data=result, harvester_version=VersionInfo.parse("0.0.0")
        )
        await converter_under_tests.convert(raw_data=result, new_ref=reference)
        # the contributors should have None as first name/last name but should have names
        assert reference.contributions[0].contributor.name == "Vincent Bichet"
        for contribution in reference.contributions:
            assert contribution.contributor.first_name is None
            assert contribution.contributor.last_name is None
            assert contribution.contributor.name is not None
        assert (
            "First names and last names are not the same length as contributors"
            in caplog.text
        )


@pytest.mark.parametrize(
    "fixture, expected_output",
    [
        ("hal_api_docs_with_date_invalid_format", "Date should be"),
        ("hal_api_docs_with_date_inconsistency", "Could not parse date"),
    ],
)
async def test_convert_with_date_exception(fixture, expected_output, caplog, request):
    """
    Test that the converter will raise an exception when the date have an unexpected format
    """
    fixture = request.getfixturevalue(fixture)
    converter_under_tests = HalReferencesConverter()
    for doc in fixture["response"]["docs"]:
        result = JsonHarvesterRawResult(
            source_identifier=doc["docid"], payload=doc, formatter_name="HAL"
        )
        reference = converter_under_tests.build(
            raw_data=result, harvester_version=VersionInfo.parse("0.0.0")
        )
        await converter_under_tests.convert(raw_data=result, new_ref=reference)
        assert reference.issued is None
        assert reference.created is None
        assert "Hal reference converter cannot create" in caplog.text
        assert expected_output in caplog.text


async def test_publication_without_files(hal_api_docs_for_researcher_with_uris: dict):
    """
    Given a list of docs where the first is a publication without files
    When the converter is called with the first doc
    Then it should return a reference with a single manifestion whith uri_s as page field


    :param hal_api_docs_for_researcher_with_uris:
    :return:
    """
    converter_under_tests = HalReferencesConverter()
    doc = hal_api_docs_for_researcher_with_uris["response"]["docs"][0]
    result = JsonHarvesterRawResult(
        source_identifier=doc["docid"], payload=doc, formatter_name="HAL"
    )
    reference = converter_under_tests.build(
        raw_data=result, harvester_version=VersionInfo.parse("0.0.0")
    )
    await converter_under_tests.convert(raw_data=result, new_ref=reference)
    assert len(reference.manifestations) == 1
    assert reference.manifestations[0].page == doc["uri_s"]


async def test_publication_with_file(hal_api_docs_for_researcher_with_uris: dict):
    """
    Given a list of docs where the second is a publication with a sigle file in fileMain_s
    When the converter is called with the second doc
    Then it should return a reference with a single manifestion whith uri_s as page field
    and the fileMain_s as download_url field

    :param hal_api_docs_for_researcher_with_uris:
    :return:
    """
    converter_under_tests = HalReferencesConverter()
    doc = hal_api_docs_for_researcher_with_uris["response"]["docs"][1]
    result = JsonHarvesterRawResult(
        source_identifier=doc["docid"], payload=doc, formatter_name="HAL"
    )
    reference = converter_under_tests.build(
        raw_data=result, harvester_version=VersionInfo.parse("0.0.0")
    )
    await converter_under_tests.convert(raw_data=result, new_ref=reference)
    assert len(reference.manifestations) == 1
    assert reference.manifestations[0].page == doc["uri_s"]
    assert reference.manifestations[0].download_url == doc["fileMain_s"]


async def test_publication_with_files(hal_api_docs_for_researcher_with_uris: dict):
    """
    Given a list of docs where the third is a publication with multiple files in files_s
    When the converter is called with the third doc
    Then it should return a reference with a single manifestion whith uri_s as page field
    and the fileMain_s as download_url field
    and the files after the first one from files_s as additional_files

    :param hal_api_docs_for_researcher_with_uris:
    :return:
    """
    converter_under_tests = HalReferencesConverter()
    doc = hal_api_docs_for_researcher_with_uris["response"]["docs"][2]
    result = JsonHarvesterRawResult(
        source_identifier=doc["docid"], payload=doc, formatter_name="HAL"
    )
    reference = converter_under_tests.build(
        raw_data=result, harvester_version=VersionInfo.parse("0.0.0")
    )
    await converter_under_tests.convert(raw_data=result, new_ref=reference)
    assert len(reference.manifestations) == 1
    assert reference.manifestations[0].page == doc["uri_s"]
    assert reference.manifestations[0].download_url == doc["fileMain_s"]
    assert len(reference.manifestations[0].additional_files) == 1
    assert reference.manifestations[0].additional_files[0] == doc["files_s"][1]
