import pytest
from semver import VersionInfo

from app.harvesters.idref.idref_basic_references_converter import (
    IdrefBasicReferencesConverter,
)
from app.harvesters.idref.persee_references_converter import PerseeReferencesConverter


@pytest.mark.asyncio
async def test_idref_convert_for_sparql_result(idref_sparql_result_for_doc):
    """
    GIVEN a IdrefReferencesConverter instance and a Idref Sparql result for a document
    WHEN the convert method is called
    THEN it should return a Reference instance with the expected values

    :param: a Idref Sparql result for a document
    :return: None
    """
    converter_under_tests = IdrefBasicReferencesConverter()

    basic_idref_source_identifier = "http://www.idref.fr/215634608/id"
    equivalent_identifiers = [
        "http://www.sudoc.fr/010658998/id",
        "http://www.sudoc.fr/126384835/id",
    ]
    expected_abstract_fr = "L'OBJECTIF DE CETTE ETUDE ETAIT D'ETABLIR LA FAISABILITE D'UN SYSTEME D'INSONORISATION DU BRUIT RAYONNE AU NIVEAU DES BOUCHES D'AERATION D'UN CLIMATISEUR AUTOMOBILE, A PARTIR DE L'UTILISATION DE TECHNIQUES DE CONTROLE ACTIF DU BRUIT DANS LES CONDUITS DE DISTRIBUTION D'AIR. UNE ETUDE SPECTRALE DES SIGNAUX ACOUSTIQUES PRESENTS DANS LE CONDUIT A PERMIS DE METTRE EN EVIDENCE DES ONDES ACOUSTIQUES CARACTERISTIQUES DE LA CONFIGURATION DU SYSTEME DE CLIMATISATION, AINSI QUE LA PRESENCE DE STRUCTURES TOURBILLONNAIRES ALEATOIRES DUES A LA GENERATION DE TURBULENCES DANS LES CONDUITS. UNE METHODOLOGIE EN TROIS ETAPES A ETE ADOPTEE: REALISATION D'UN SYSTEME DE CONTROLE ACTIF POUR ATTENUER LE BRUIT RAYONNE PAR LES SOURCES DETERMINISTES. POUR CE FAIRE, A PARTIR D'UNE EXPERIENCE DE LABORATOIRE NOUS AVONS COMPARE LES PERFORMANCES DE DIFFERENTS ALGORITHMES DE CONTROLE: TYPES LMS (METHODE DU TYPE DES MOINDRES CARRES) ET GMV (VARIANCE MINIMALE GENERALISEE). CETTE COMPARAISON A D'ABORD ETE EFFECTUEE AU MOYEN DE SIMULATIONS UTILISANT LES FONCTIONS DE TRANSFERTS REELLES DU CONDUIT, ET ENSUITE SUR LE SYSTEME EXPERIMENTAL LUI MEME. ANALYSE DE LA TURBULENCE PRESENTE DANS LES CONDUITS, AFIN DE REALISER UN SYSTEME PASSIF EN FORME DE GRILLE. CELUI-CI A PERMIS UN RECONDITIONNEMENT SPECTRAL DE L'ENERGIE CINETIQUE DE LA TURBULENCE, ET UNE MODIFICATION DE LA REPARTITION SPECTRALE DE LA PRESSION ACOUSTIQUE ASSOCIEE A CES SOURCES LOCALES. LES PRINCIPAUX BENEFICES DE CETTE TECHNIQUE ONT ETE, LA DIMINUTION DU NIVEAU SONORE GLOBAL, ET SURTOUT L'AMELIORATION DE LA COHERENCE ENTRE DEUX POINTS DE MESURE. CE DERNIER POINT A NOTAMMENT PERMIS D'OPTIMISER LES PERFORMANCES DU CONTROLE ACTIF. L'APPLICATION DE CE CONTROLE ACTIF ET PASSIF SUR LE SYSTEME DE CLIMATISATION, AFIN DE CONFIRMER LA VALIDITE DE LA METHODOLOGIE UTILISEE. DES RESULTATS EXPERIMENTAUX, OBTENUS A PARTIR DU SYSTEME COMPLET, ONT ETE PRESENTES ET ANALYSES"

    expected_abstract_language = "fr"
    expected_title = "Insonorisation d'un système de climatisation automobile par contrôle actif du bruit"
    expected_document_type = "Work"
    expected_auth_name = "Jean-Louis Abatut"
    expected_auth_first_name = "Jean-Louis"
    expected_auth_last_name = "Abatut"

    test_reference = converter_under_tests.build(
        raw_data=idref_sparql_result_for_doc,
        harvester_version=VersionInfo.parse("0.0.0"),
    )
    assert test_reference.source_identifier == basic_idref_source_identifier
    await converter_under_tests.convert(
        raw_data=idref_sparql_result_for_doc, new_ref=test_reference
    )
    assert expected_title == test_reference.titles[0].value
    assert expected_abstract_fr in test_reference.abstracts[0].value
    assert expected_abstract_language == test_reference.abstracts[0].language
    assert any(
        document_type.label == expected_document_type
        for document_type in test_reference.document_type
    )
    assert len(test_reference.contributions) == 1
    assert expected_auth_name == test_reference.contributions[0].contributor.name
    assert (
        expected_auth_first_name
        == test_reference.contributions[0].contributor.first_name
    )
    assert (
        expected_auth_last_name == test_reference.contributions[0].contributor.last_name
    )
    assert len(test_reference.identifiers) == 3
    assert test_reference.identifiers[0].value == basic_idref_source_identifier
    assert test_reference.identifiers[1].value in equivalent_identifiers
    assert test_reference.identifiers[2].value in equivalent_identifiers
    assert test_reference.identifiers[1].value != test_reference.identifiers[2].value
