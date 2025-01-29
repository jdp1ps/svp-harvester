"""
Test the validate_reference decorator of the AbstractReferencesConverter class.
"""

import pytest

from app.db.models.abstract import Abstract as DbAbstract
from app.db.models.contribution import Contribution as DbContribution
from app.db.models.contributor import Contributor as DbContributor
from app.db.models.reference import Reference as DbReference
from app.db.models.subtitle import Subtitle as DbSubtitle
from app.db.models.title import Title as DbTitle
from app.harvesters.abstract_references_converter import AbstractReferencesConverter


@pytest.fixture(name="reference_without_title")
def fixture_reference_without_title():
    """
    Return a reference without title
    """
    return DbReference(
        source_identifier="I am unique !",
        harvester="test_harvester",
        titles=[],
    )


@pytest.fixture(name="reference_without_harvester")
def fixture_reference_without_harvester():
    """
    Return a reference without harvester
    """
    return DbReference(
        source_identifier="I am unique !",
        harvester="",
        titles=[DbTitle(value="I am a title")],
    )


@pytest.fixture(name="reference_with_abstract_value_none")
def fixture_reference_with_abstract_value_none():
    """
    Return a reference without harvester
    """
    return DbReference(
        source_identifier="I am unique !",
        harvester="test",
        titles=[DbTitle(value="I am a title")],
        abstracts=[],
    )


@pytest.fixture(name="reference_without_identifier")
def fixture_reference_without_identifier():
    """
    Return a reference without identifier
    """
    return DbReference(
        titles=[DbTitle(value="I am a title")],
    )


@pytest.fixture(name="reference_with_all_fields")
def fixture_reference_with_all_fields():
    """
    Return a reference with all the fields set.
    """
    return DbReference(
        source_identifier="I am unique !",
        titles=[DbTitle(value="I am a title")],
        harvester="test_harvester",
        abstracts=[DbAbstract(value="I am an abstract")],
        subtitles=[DbSubtitle(value="I am a subtitle")],
        document_type=["I am a document type"],
        contributions=[
            DbContribution(
                rank=1,
                role=DbContribution.get_url("AUT"),
                contributor=DbContributor(
                    source="I am a source",
                    source_identifier="I am a source identifier",
                    name="I am a name",
                    first_name="I am a first name",
                    last_name="I am a last name",
                    name_variants=["I am a name variant"],
                    structured_name_variants=[
                        {
                            "first_name": "I am a first name variant",
                            "last_name": "I am a last name variant",
                        }
                    ],
                ),
            )
        ],
    )


@pytest.mark.asyncio
async def test_reference_without_title_raises_exception(reference_without_title):
    """
    Given a reference without title
    When the validate_reference decorator is called
    Then an AssertionError should be raised

    :param reference_without_title: A reference without title
    """

    async def decorated_function(self, new_ref):
        return reference_without_title

    function_with_decorator = AbstractReferencesConverter.validate_reference(
        decorated_function
    )
    with pytest.raises(AssertionError) as exc_info:
        await function_with_decorator(
            AbstractReferencesConverter, new_ref=reference_without_title
        )

    assert exc_info.match("titles should be set on reference")


@pytest.mark.asyncio
async def test_reference_without_identifier_raises_exception(
    reference_without_identifier,
):
    """ "
    Given a reference without identifier
    When the validate_reference decorator is called
    Then an AssertionError should be raised

    :param reference_without_identifier: A reference without identifier
    """

    async def decorated_function(self, new_ref):
        return None

    function_with_decorator = AbstractReferencesConverter.validate_reference(
        decorated_function
    )
    with pytest.raises(AssertionError) as exc_info:
        await function_with_decorator(
            AbstractReferencesConverter, new_ref=reference_without_identifier
        )

    assert exc_info.match("Source identifier should be set on reference")


@pytest.mark.asyncio
async def test_reference_without_harvester_raises_exception(
    reference_without_harvester,
):
    """ "
    Given a reference without identifier
    When the validate_reference decorator is called
    Then an AssertionError should be raised

    :param reference_without_harvester: A reference without identifier
    """

    async def decorated_function(self, new_ref):
        return None

    function_with_decorator = AbstractReferencesConverter.validate_reference(
        decorated_function
    )
    with pytest.raises(AssertionError) as exc_info:
        await function_with_decorator(
            AbstractReferencesConverter, new_ref=reference_without_harvester
        )

    assert exc_info.match("harvester should be set on reference")


@pytest.mark.asyncio
async def test_reference_with_abstract_value_none_raises_exception(
    reference_with_abstract_value_none,
):
    """
    Given a reference without identifier
    When the validate_reference decorator is called
    Then an AssertionError should be raised

    :param reference_with_abstract_value_none: A reference without identifier
    """

    async def decorated_function(self, new_ref):
        reference_with_abstract_value_none.__dict__["abstracts"] = None

    function_with_decorator = AbstractReferencesConverter.validate_reference(
        decorated_function
    )
    with pytest.raises(AssertionError) as exc_info:
        await function_with_decorator(
            AbstractReferencesConverter, new_ref=reference_with_abstract_value_none
        )

    assert exc_info.match("abstracts should be set on reference")


@pytest.mark.asyncio
async def test_reference_with_all_fields_does_not_raise_exception(
    reference_with_all_fields,
):
    """
    Given a reference with title and identifier
    When the validate_reference decorator is called
    Then the reference should be returned

    :param reference_with_all_fields:
    """

    async def decorated_function(self, new_ref):
        return None

    function_with_decorator = AbstractReferencesConverter.validate_reference(
        decorated_function
    )
    await function_with_decorator(
        AbstractReferencesConverter, new_ref=reference_with_all_fields
    )

    assert True, "No exception should be raised"
