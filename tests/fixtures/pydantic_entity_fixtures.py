import pytest

from app.models.people import Person as PydanticPerson
from tests.fixtures.common import _person_from_json_data, _person_json_data_from_file


@pytest.fixture(name="person_without_identifiers")
def fixture_person_without_identifiers(
    person_without_identifiers_json,
) -> PydanticPerson:
    """
    Generate a person with only first name and last name in Pydantic format
    :return: person with only first name and last name in Pydantic format
    """
    return _person_from_json_data(person_without_identifiers_json)


@pytest.fixture(name="person_without_identifiers_json")
def fixture_person_without_identifiers_json(_base_path) -> dict:
    """
    Generate a person with only first name and last name in JSON format
    :param _base_path: test data directory base
    :return: person with only first name and last name in JSON format
    """
    return _person_json_data_from_file(_base_path, "person_without_identifier")


@pytest.fixture(name="person_with_name_and_orcid")
def fixture_person_with_name_and_orcid(
    person_with_name_and_orcid_json,
) -> PydanticPerson:
    """
    Generate a person with first name, last name and ORCID in Pydantic format
    :return: person with first name, last name and ORCID  in Pydantic format
    """
    return _person_from_json_data(person_with_name_and_orcid_json)


@pytest.fixture(name="person_with_name_and_orcid_json")
def fixture_person_with_name_and_orcid_json(_base_path) -> dict:
    """
    Generate a person with first name, last name and ORCID in Json format
    :param _base_path: test data directory base
    :return: person with first name, last name and ORCID in Json format
    """
    return _person_json_data_from_file(_base_path, "person_with_name_and_orcid")


@pytest.fixture(name="person_with_name_and_idref")
def fixture_person_with_name_and_idref(
    person_with_name_and_idref_json,
) -> PydanticPerson:
    """
    Generate a person with first name, last name and IDREF in Pydantic format
    :return: person with first name, last name and IDREF  in Pydantic format
    """
    return _person_from_json_data(person_with_name_and_idref_json)


@pytest.fixture(name="person_with_name_and_idref_json")
def fixture_person_with_name_and_idref_json(_base_path) -> dict:
    """
    Generate a person with first name, last name and IDREF in Json format
    :param _base_path: test data directory base
    :return: person with first name, last name and IDREF in Json format
    """
    return _person_json_data_from_file(_base_path, "person_with_name_and_idref")


@pytest.fixture(name="person_with_name_and_id_hal_i")
def fixture_person_with_name_and_id_hal_i(
    person_with_name_and_id_hal_i_json,
) -> PydanticPerson:
    """
    Generate a person with first name, last name and ID_HAL_I in Pydantic format
    :return: person with first name, last name and ID_HAL_I  in Pydantic format
    """
    return _person_from_json_data(person_with_name_and_id_hal_i_json)


@pytest.fixture(name="person_with_name_and_id_hal_i_json")
def fixture_person_with_name_and_id_hal_i_json(_base_path) -> dict:
    """
    Generate a person with first name, last name and ID_HAL_I in Json format
    :param _base_path: test data directory base
    :return: person with first name, last name and ID_HAL_I in Json format
    """
    return _person_json_data_from_file(_base_path, "person_with_name_and_id_hal_i")


@pytest.fixture(name="person_with_name_and_id_hal_s")
def fixture_person_with_name_and_id_hal_s(
    person_with_name_and_id_hal_s_json,
) -> PydanticPerson:
    """
    Generate a person with first name, last name and ID_HAL_I in Pydantic format
    :return: person with first name, last name and ID_HAL_I  in Pydantic format
    """
    return _person_from_json_data(person_with_name_and_id_hal_s_json)


@pytest.fixture(name="person_with_name_and_scopus_eid")
def fixture_person_with_name_and_scopus_eid(
    person_with_name_and_scopus_eid_json,
) -> PydanticPerson:
    """
    Generate a person with first name, last name and EID in Pydantic format
    :return: person with first name, last name and EID in Pydantic format
    """
    return _person_from_json_data(person_with_name_and_scopus_eid_json)


@pytest.fixture(name="person_with_name_and_id_hal_s_json")
def fixture_person_with_name_and_id_hal_s_json(_base_path) -> dict:
    """
    Generate a person with first name, last name and ID_HAL_S in Json format
    :param _base_path: test data directory base
    :return: person with first name, last name and ID_HAL_S in Json format
    """
    return _person_json_data_from_file(_base_path, "person_with_name_and_id_hal_s")


@pytest.fixture(name="person_with_name_and_unknown_identifier_type_json")
def fixture_person_with_name_and_unknown_identifier_type_json(_base_path) -> dict:
    """
    Generate a person with first name, last name and unknown identifier type in Json format
    :param _base_path: test data directory base
    :return: person with first name, last name and unknown identifier type in Json format
    """
    return _person_json_data_from_file(
        _base_path, "person_with_name_and_unknown_identifier_type"
    )


@pytest.fixture(name="person_with_name_and_scopus_eid_json")
def fixture_person_with_name_and_scopus_eid_json(_base_path) -> dict:
    """
    Generate a person with first name, last name and EID in Json format
    :param _base_path: test data directory base
    :return: person with first name, last name and EID in Json format
    """
    return _person_json_data_from_file(_base_path, "person_with_name_and_scopus_eid")


@pytest.fixture(name="person_with_name_and_invalid_idref")
def fixture_person_with_name_and_invalid_idref(
    person_with_name_and_invalid_idref_json,
) -> PydanticPerson:
    """
    Generate a person with first name, last name and IDREF in Pydantic format
    :return: person with first name, last name and IDREF  in Pydantic format
    """
    return _person_from_json_data(person_with_name_and_invalid_idref_json)


@pytest.fixture(name="person_with_name_and_invalid_idref_json")
def fixture_person_with_name_and_invalid_idref_json(_base_path) -> dict:
    """
    Generate a person with first name, last name and IDREF in Json format
    :param _base_path: test data directory base
    :return: person with first name, last name and IDREF in Json format
    """
    return _person_json_data_from_file(_base_path, "person_with_name_and_invalid_idref")
