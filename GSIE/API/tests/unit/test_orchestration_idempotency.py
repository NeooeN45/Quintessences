"""Contrats purs de l'idempotence de l'orchestration."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from gsie_api.engines.orchestration.idempotency import (
    AnalyseIdempotencyConflictError,
    _retirer_champs_calcules,
    _verrouiller,
    charger_analyse_idempotente,
    empreinte_requete,
)
from gsie_api.engines.orchestration.schemas import AnalyseRequest
from gsie_api.engines.orchestration.service import OrchestrationEngine


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


def test_retirer_champs_calcules_ne_modifie_pas_la_preuve_source() -> None:
    contenu = {
        "recommandations": {
            "recommandations": [
                None,
                {
                    "contournable": True,
                    "alternatives": [None, {"contournable": False, "nom": "chêne"}],
                },
            ]
        }
    }

    nettoye = _retirer_champs_calcules(contenu)

    assert "contournable" not in nettoye["recommandations"]["recommandations"][1]
    assert "contournable" not in nettoye["recommandations"]["recommandations"][1]["alternatives"][1]
    assert "contournable" in contenu["recommandations"]["recommandations"][1]


def test_retirer_champs_calcules_ignore_les_blocs_de_forme_inattendue() -> None:
    assert _retirer_champs_calcules({}) == {}
    assert _retirer_champs_calcules({"recommandations": {}}) == {"recommandations": {}}


@pytest.mark.asyncio
async def test_verrouille_une_cle_sur_postgresql() -> None:
    session = MagicMock()
    session.bind = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))
    session.execute = AsyncMock()

    await _verrouiller(session, "requete-1")

    session.execute.assert_awaited_once()
    assert session.execute.await_args.args[0].text.startswith("SELECT pg_advisory_xact_lock")


@pytest.mark.asyncio
async def test_retourne_une_empreinte_quand_aucune_preuve_n_existe() -> None:
    session = MagicMock()
    session.execute = AsyncMock()
    resultat = MagicMock()
    resultat.scalars.return_value.first.return_value = None
    session.execute.return_value = resultat
    requete = _requete()

    preuve, empreinte = await charger_analyse_idempotente(session, requete)

    assert preuve is None
    assert empreinte == empreinte_requete(requete)


@pytest.mark.asyncio
async def test_refuse_une_preuve_historique_sans_empreinte() -> None:
    session = MagicMock()
    session.execute = AsyncMock()
    resultat = MagicMock()
    existante = MagicMock(requete_fingerprint=None)
    resultat.scalars.return_value.first.return_value = existante
    session.execute.return_value = resultat

    with pytest.raises(AnalyseIdempotencyConflictError, match="sans empreinte"):
        await charger_analyse_idempotente(session, _requete())


@pytest.mark.asyncio
async def test_refuse_une_requete_dont_l_empreinte_a_change() -> None:
    session = MagicMock()
    session.execute = AsyncMock()
    resultat = MagicMock()
    existante = MagicMock(requete_fingerprint="empreinte-inconnue")
    resultat.scalars.return_value.first.return_value = existante
    session.execute.return_value = resultat

    with pytest.raises(AnalyseIdempotencyConflictError, match="contenu différent"):
        await charger_analyse_idempotente(session, _requete())


@pytest.mark.asyncio
async def test_rejoue_une_preuve_dont_l_empreinte_est_identique() -> None:
    session = MagicMock()
    session.execute = AsyncMock()
    resultat = MagicMock()
    preuve = object()
    requete = _requete()
    resultat.scalars.return_value.first.return_value = MagicMock(
        requete_fingerprint=empreinte_requete(requete), contenu={}
    )
    session.execute.return_value = resultat

    with patch(
        "gsie_api.engines.orchestration.idempotency.AnalyseComplete.model_validate",
        return_value=preuve,
    ):
        obtenu, empreinte = await charger_analyse_idempotente(session, requete)

    assert obtenu is preuve
    assert empreinte == empreinte_requete(requete)


@pytest.mark.asyncio
async def test_rejoue_une_preuve_existante_sans_reexecuter_les_moteurs() -> None:
    requete = _requete()
    existante = MagicMock()
    engine = OrchestrationEngine(MagicMock())

    with (
        patch(
            "gsie_api.engines.orchestration.service.charger_analyse_idempotente",
            new=AsyncMock(return_value=(existante, "empreinte")),
        ),
        patch.object(engine, "analyser", new=AsyncMock()) as analyser,
    ):
        resultat = await engine.analyser_idempotente(requete, datetime.now(UTC))

    assert resultat is existante
    analyser.assert_not_awaited()


@pytest.mark.asyncio
async def test_transmet_l_empreinte_sur_une_nouvelle_analyse() -> None:
    requete = _requete()
    engine = OrchestrationEngine(MagicMock())
    resultat = object()
    maintenant = datetime.now(UTC)

    with (
        patch(
            "gsie_api.engines.orchestration.service.charger_analyse_idempotente",
            new=AsyncMock(return_value=(None, "empreinte")),
        ),
        patch.object(engine, "analyser", new=AsyncMock(return_value=resultat)) as analyser,
    ):
        obtenu = await engine.analyser_idempotente(requete, maintenant)

    assert obtenu is resultat
    analyser.assert_awaited_once_with(requete, maintenant, requete_fingerprint="empreinte")


@pytest.mark.asyncio
async def test_analyser_persiste_une_preuve_avec_un_identifiant_uuid() -> None:
    requete = _requete()
    inference = MagicMock(conclusions=[MagicMock()])
    diagnostic = MagicMock(diagnostic_id=uuid4())
    recommandations = MagicMock()
    validation = MagicMock()
    resultat = MagicMock(analyse_id=uuid4(), requete_origine=requete.requete_id, resume={})
    engine = OrchestrationEngine(MagicMock())
    engine._qualifier = MagicMock(return_value=[])
    persister = AsyncMock()

    with (
        patch("gsie_api.engines.orchestration.service.ReasoningEngine") as reasoning_cls,
        patch("gsie_api.engines.orchestration.service.DiagnosticEngine") as diagnostic_cls,
        patch(
            "gsie_api.engines.orchestration.service.DiagnosticRequest",
            return_value=MagicMock(),
        ),
        patch("gsie_api.engines.orchestration.service.RecommendationEngine") as recommendation_cls,
        patch("gsie_api.engines.orchestration.service.ValidationEngine") as validation_cls,
        patch(
            "gsie_api.engines.orchestration.service.AnalyseComplete",
            return_value=resultat,
        ),
        patch(
            "gsie_api.engines.orchestration.service.ensemble_complet_to_validation_request",
            return_value=MagicMock(),
        ),
        patch.object(engine, "_persister_analyse", new=persister),
    ):
        reasoning_cls.return_value.infer = AsyncMock(return_value=inference)
        diagnostic_cls.return_value.diagnostiquer = AsyncMock(return_value=diagnostic)
        recommendation_cls.return_value.recommend = AsyncMock(return_value=recommandations)
        validation_cls.return_value.validate = AsyncMock(return_value=validation)

        obtenu = await engine.analyser(requete, datetime.now(UTC), requete_fingerprint="empreinte")

    assert obtenu is resultat
    persister.assert_awaited_once_with(
        resultat,
        requete.station_id,
        persister.await_args.args[2],
        requete_fingerprint="empreinte",
    )
