import pytest
from semver import VersionInfo

from app.db.daos.contributor_dao import ContributorDAO
from app.db.session import async_session
from app.harvesters.hal.hal_references_converter import HalReferencesConverter
from app.harvesters.json_harvester_raw_result import JsonHarvesterRawResult


@pytest.fixture(name="hal_api_docs_with_contributor_identifiers_content")
def fixture_hal_api_docs_with_contributor_identifiers_content(
    hal_api_docs_with_contributor_identifiers,
):
    """Return the list of document references from hal response"""
    return hal_api_docs_with_contributor_identifiers["response"]["docs"]


async def test_convert(
    hal_api_docs_with_contributor_identifiers_content,
):  # pylint: disable=too-many-locals
    """Test that the converter will return normalised references"""
    converter_under_tests = HalReferencesConverter()

    doc_0 = hal_api_docs_with_contributor_identifiers_content[0]
    result = JsonHarvesterRawResult(
        source_identifier=doc_0["docid"], payload=doc_0, formatter_name="HAL"
    )
    test_reference = converter_under_tests.build(
        raw_data=result, harvester_version=VersionInfo.parse("0.0.0")
    )
    await converter_under_tests.convert(raw_data=result, new_ref=test_reference)
    contribution = test_reference.contributions[0]
    contributor_id = contribution.contributor.id
    assert contributor_id is not None
    assert isinstance(contributor_id, int)
    async with async_session() as session:
        async with session.begin_nested():
            contributor = await ContributorDAO(session).get_by_id(contributor_id)
            assert contributor is not None
            assert len(contributor.identifiers) == 6
            assert any(
                [
                    identifier.type == "orcid"
                    and identifier.value == "https://orcid.org/0000-0002-3053-9512"
                    for identifier in contributor.identifiers
                ]
            )
            assert any(
                [
                    identifier.type == "isni"
                    and identifier.value == "http://isni.org/isni/0000000071437032"
                    for identifier in contributor.identifiers
                ]
            )
            assert any(
                [
                    identifier.type == "google_scholar"
                    and identifier.value
                    == "https://scholar.google.fr/citations?user=_88eIccAAAAJ"
                    for identifier in contributor.identifiers
                ]
            )
            assert any(
                [
                    identifier.type == "idhal_i" and identifier.value == "1288873"
                    for identifier in contributor.identifiers
                ]
            )
            assert any(
                [
                    identifier.type == "idref"
                    and identifier.value == "https://www.idref.fr/121561712"
                    for identifier in contributor.identifiers
                ]
            )
            assert any(
                [
                    identifier.type == "viaf"
                    and identifier.value == "https://viaf.org/viaf/56924466"
                    for identifier in contributor.identifiers
                ]
            )
