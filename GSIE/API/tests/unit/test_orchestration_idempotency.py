"""Contrats purs de l'idempotence de l'orchestration."""

from uuid import uuid4

from gsie_api.engines.orchestration.idempotency import empreinte_requete
from gsie_api.engines.orchestration.schemas import AnalyseRequest


def _requete() -> AnalyseRequest:
    source = {
        "type_source": "referentiel_officiel",
        "auteur": "INRAE (2008)",
        "date_publication": "2008",
        "reference": "Référentiel pédologique français, édition 2008",
    }
    return AnalyseRequest.model_validate(
        {
            "requete_id": str(uuid4()),
            "station_id": str(uuid4()),
            "contexte": {
                "pedologie": {
                    "source_moteur": "PEDOLOGY",
                    "source": source,
                    "evidence_level": "B",
                    "valeurs": {"pH": 5.2, "profondeur_cm": 80},
                }
            },
            "regles": [
                {
                    "identifiant": "regle-acidite-01",
                    "condition": "pedologie_pH < 5.5",
                    "enonce_conclusion": "Le sol est acide.",
                    "source": source,
                    "evidence_level": "B",
                    "niveau_confiance": 0.85,
                }
            ],
            "qualifications": [
                {
                    "identifiant_regle": "regle-acidite-01",
                    "role": "contrainte",
                    "domaine_element": "pedologique",
                }
            ],
            "etat_global": {
                "etat": "vigueur_reduite",
                "justification": "Acidité constatée",
                "source": source,
                "evidence_level": "B",
            },
            "question": "Quelle essence est adaptée ?",
            "objectif_forestier": "production",
        }
    )


def test_empreinte_est_stable_pour_la_meme_requete() -> None:
    requete = _requete()
    assert empreinte_requete(requete) == empreinte_requete(
        AnalyseRequest.model_validate(requete.model_dump(mode="json"))
    )


def test_empreinte_change_si_le_contrat_change() -> None:
    requete = _requete()
    modifiee = requete.model_copy(update={"question": "Quelle essence favoriser ?"})
    assert empreinte_requete(requete) != empreinte_requete(modifiee)
