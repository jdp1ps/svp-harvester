"""Tests for the Person model."""
import pytest
from pydantic import ValidationError

from app.models.people import Person


def test_person_without_identifiers(person_without_identifiers: Person):
    """
    GIVEN a person without identifiers
    WHEN the person is created
    THEN check the person has the correct attributes
    :param person_without_identifiers: person without identifiers
    """
    assert person_without_identifiers.name == "John Doe"
    assert person_without_identifiers.get_identifier("idref") is None
    assert person_without_identifiers.has_no_bibliographic_identifiers()


def test_person_with_name_and_idref(person_with_name_and_idref: Person):
    """
    GIVEN a person with name and IDREF
    WHEN the person is created
    THEN check the person has the correct attributes
    :param person_with_name_and_idref: person with name and IDREF
    """
    assert person_with_name_and_idref.name == "John Doe"
    assert person_with_name_and_idref.get_identifier("idref") == "123456789"
    assert not person_with_name_and_idref.has_no_bibliographic_identifiers()


def test_person_with_invalid_identifier(
    person_with_name_and_unknown_identifier_type_json: dict,
):
    """
    GIVEN a person with name and unknown identifier type
    WHEN the person is created
    THEN check a validation error is raised
    """
    with pytest.raises(ValidationError, match="Invalid identifiers: foobar"):
        Person(**person_with_name_and_unknown_identifier_type_json)


def test_person_with_last_name_only():
    """
    GIVEN a person with only last name
    WHEN the person is created
    THEN check a validation error is raised
    """
    with pytest.raises(
        ValidationError,
        match="At least one identifier or the entire name must be provided",
    ):
        Person(last_name="Doe")
