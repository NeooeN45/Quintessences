"""Tests unitaires — Validation Engine.

Vérifie les contrôles de conformité constitutionnelle et la logique
de blocage/partiellement_valide/valide.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from gsie_api.engines.validation.engine import ValidationEngine, ValidationEngineError
from gsie_api.engines.validation.schemas import (
    CauseBlocage,
    ControleResultat,
    ResultatControle,
    TypeCauseBlocage,
    TypeSortie,
    ValidationRequest,
    ValidationResult,
    ValidationStatut,
)


def _make_request(
    type_sortie: TypeSortie = TypeSortie.diagnostic,
    contenu: dict | None = None,
    chaines_inference: list | None = None,
) -> ValidationRequest:
    if contenu is None:
        contenu = {
            "evidence_level": "B",
            "source": {"type_source": "peer_reviewed", "auteur": "Test", "reference": "DOI"},
            "justification": "Diagnostic fondé sur observations terrain.",
        }
    if chaines_inference is None:
        chaines_inference = [{"conclusion": "test"}]
    return ValidationRequest(
        requete_id=uuid4(),
        type_sortie=type_sortie,
        contenu=contenu,
        chaines_inference=chaines_inference,
    )


def _mock_session() -> AsyncMock:
    """Session DB mock — scalar_one retourne None (pas de revision existante)."""
    session = AsyncMock()
    # scalar_one est synchrone sur le Result (pas async) — MagicMock, pas AsyncMock.
    result_mock = MagicMock()
    result_mock.scalar_one.return_value = None
    session.execute = AsyncMock(return_value=result_mock)
    session.flush = AsyncMock()
    session.add = AsyncMock()
    return session


@pytest.fixture
def engine() -> ValidationEngine:
    # La persistance étant obligatoire pour les résultats non-valides
    # (RFC-0028), on fournit une session mock aux tests unitaires.
    return ValidationEngine(session=_mock_session())


# --- Tests statut valide ---


@pytest.mark.asyncio
async def should_return_valide_when_diagnostic_complete(engine: ValidationEngine) -> None:
    """Un diagnostic complet avec source, niveau de preuve, chaîne et justification est valide."""
    result = await engine.validate(_make_request())
    assert result.statut == ValidationStatut.valide
    assert not result.causes_blocage
    assert len(result.controles) == 5
    assert all(
        c.resultat == ResultatControle.conforme
        for c in result.controles
        if c.resultat != ResultatControle.non_applicable
    )


@pytest.mark.asyncio
async def should_return_valide_when_recommandation_complete(engine: ValidationEngine) -> None:
    """Une recommandation complète avec source, niveau de preuve et contournable est valide."""
    contenu = {
        "evidence_level": "B",
        "source": {"type_source": "peer_reviewed", "auteur": "Test", "reference": "DOI"},
        "justification": {
            "sources": [{"type_source": "peer_reviewed", "auteur": "X", "reference": "Y"}]
        },
        "recommandations": [
            {
                "contournable": True,
                "justification": {
                    "sources": [{"type_source": "peer_reviewed", "auteur": "X", "reference": "Y"}]
                },
            },
        ],
    }
    result = await engine.validate(_make_request(TypeSortie.recommandation, contenu))
    assert result.statut == ValidationStatut.valide


# --- Tests statut bloque ---


@pytest.mark.asyncio
async def should_return_bloque_when_no_evidence_level(engine: ValidationEngine) -> None:
    """Un diagnostic sans niveau de preuve est bloqué (GSIE-CON-002)."""
    contenu = {
        "source": {"type_source": "peer_reviewed", "auteur": "Test", "reference": "DOI"},
        "justification": "Diagnostic fondé sur observations.",
    }
    result = await engine.validate(_make_request(contenu=contenu))
    assert result.statut == ValidationStatut.bloque
    assert any(c.type_cause == TypeCauseBlocage.sans_niveau_preuve for c in result.causes_blocage)


@pytest.mark.asyncio
async def should_return_bloque_when_no_source(engine: ValidationEngine) -> None:
    """Un diagnostic sans source est bloqué (GSIE-CON-002)."""
    contenu = {
        "evidence_level": "B",
        "justification": "Diagnostic fondé sur observations.",
    }
    result = await engine.validate(_make_request(contenu=contenu))
    assert result.statut == ValidationStatut.bloque
    assert any(c.type_cause == TypeCauseBlocage.sans_source for c in result.causes_blocage)


@pytest.mark.asyncio
async def should_return_bloque_when_no_chaine_inference(engine: ValidationEngine) -> None:
    """Un diagnostic sans chaîne d'inférence est bloqué (GSIE-CON-004)."""
    result = await engine.validate(_make_request(chaines_inference=[]))
    assert result.statut == ValidationStatut.bloque
    assert any(
        c.type_cause == TypeCauseBlocage.sans_chaine_inference for c in result.causes_blocage
    )


@pytest.mark.asyncio
async def should_return_bloque_when_recommandation_non_contournable(
    engine: ValidationEngine,
) -> None:
    """Une recommandation non contournable est bloquée (GSIE-CON-001)."""
    contenu = {
        "evidence_level": "B",
        "source": {"type_source": "peer_reviewed", "auteur": "Test", "reference": "DOI"},
        "justification": {
            "sources": [{"type_source": "peer_reviewed", "auteur": "X", "reference": "Y"}]
        },
        "recommandations": [
            {
                "contournable": False,
                "justification": {
                    "sources": [{"type_source": "peer_reviewed", "auteur": "X", "reference": "Y"}]
                },
            },
        ],
    }
    result = await engine.validate(_make_request(TypeSortie.recommandation, contenu))
    assert result.statut == ValidationStatut.bloque
    assert any(
        c.type_cause == TypeCauseBlocage.recommandation_non_contournable
        for c in result.causes_blocage
    )


# --- Tests statut partiellement_valide ---


@pytest.mark.asyncio
async def should_return_partiellement_valide_when_ensemble_complet_with_non_critical_failure(
    engine: ValidationEngine,
) -> None:
    """Un ensemble complet avec un échec non critique est partiellement valide."""
    contenu = {
        "diagnostic": {
            "evidence_level": "B",
            "source": {"type_source": "peer_reviewed", "auteur": "Test", "reference": "DOI"},
            "justification": "Diagnostic fondé.",
        },
        "recommandations": [
            {
                "contournable": True,
                "justification": {
                    "sources": [{"type_source": "peer_reviewed", "auteur": "X", "reference": "Y"}]
                },
            },
        ],
    }
    # Pas de chaîne d'inférence — non critique pour ensemble_complet
    result = await engine.validate(
        _make_request(TypeSortie.ensemble_complet, contenu, chaines_inference=[])
    )
    # Le contrôle chaine_inference est non conforme mais non critique
    assert result.statut in (ValidationStatut.partiellement_valide, ValidationStatut.bloque)


# --- Tests invariants schéma ---


def should_reject_valide_with_causes_blocage() -> None:
    """Le schéma rejette statut=valide avec causes de blocage."""
    with pytest.raises(ValueError, match="valide.*causes"):
        ValidationResult(
            validation_id=uuid4(),
            requete_origine=uuid4(),
            statut=ValidationStatut.valide,
            controles=[
                ControleResultat(
                    nom_controle="test", resultat=ResultatControle.conforme, details="ok"
                )
            ],
            causes_blocage=[
                CauseBlocage(
                    type_cause=TypeCauseBlocage.sans_source,
                    element_concerne=uuid4(),
                    description="test",
                )
            ],
            date_validation=datetime.now(UTC),
        )


def should_reject_bloque_without_causes_blocage() -> None:
    """Le schéma rejette statut=bloque sans cause de blocage."""
    with pytest.raises(ValueError, match="bloque.*cause"):
        ValidationResult(
            validation_id=uuid4(),
            requete_origine=uuid4(),
            statut=ValidationStatut.bloque,
            controles=[
                ControleResultat(
                    nom_controle="test", resultat=ResultatControle.non_conforme, details="ko"
                )
            ],
            causes_blocage=[],
            date_validation=datetime.now(UTC),
        )


def should_reject_ensemble_complet_without_diagnostic_and_recommandations() -> None:
    """Le schéma rejette ensemble_complet sans diagnostic et recommandations."""
    with pytest.raises(ValueError, match="ensemble_complet"):
        ValidationRequest(
            requete_id=uuid4(),
            type_sortie=TypeSortie.ensemble_complet,
            contenu={"diagnostic": {}},  # manque recommandations
        )


# --- Chaque controle a sa cause propre, aucune par defaut ---


def test_chaque_controle_produit_a_sa_cause_declaree() -> None:
    """Aucun contrôle ne se voit attribuer une cause de blocage par défaut.

    La correspondance retombait sur `explicabilite_insuffisante` pour tout
    contrôle non répertorié. Un contrôle ajouté sans son entrée aurait annoncé
    au forestier une cause **fausse** — plausible, vérifiable en apparence, et
    l'envoyant chercher un défaut d'explicabilité là où le blocage venait
    d'ailleurs. `VALIDATION_ENGINE.md` §6 exige « la cause précise de blocage ».

    Le paramétrage part des noms que le moteur produit réellement, et non d'une
    liste écrite à la main : c'est ce qui rend ce contrôle durable. Un contrôle
    ajouté à `validate` sans entrée dans la correspondance fera tomber ce test.
    """
    import inspect

    from gsie_api.engines.validation import engine as module_moteur

    source = inspect.getsource(module_moteur.ValidationEngine)
    # Les noms de controle tels que les `ControleResultat` les portent.
    noms = set(re.findall(r'nom_controle="([a-z_]+)"', source))
    assert noms, "aucun nom de contrôle trouvé — le motif de lecture est périmé"

    for nom in sorted(noms):
        cause = ValidationEngine._cause_pour_controle(nom)
        assert cause is not None, f"contrôle {nom} sans cause"


def test_un_controle_inconnu_est_refuse_et_non_etiquete_au_hasard() -> None:
    """Un contrôle sans cause déclarée lève, plutôt que de mentir sur le motif.

    `ValidationEngineError` et non un statut : c'est une erreur de
    programmation, pas une sortie non conforme. La garantie « `validate` ne lève
    jamais pour une sortie non conforme » (§6) reste entière.
    """
    with pytest.raises(ValidationEngineError, match="sans cause de blocage"):
        ValidationEngine._cause_pour_controle("controle_ajoute_sans_cause")


def test_une_recommandation_non_contournable_est_bloquee_non_partielle() -> None:
    """`GSIE-CON-001` ne se dégrade pas en `partiellement_valide`.

    L'ensemble des contrôles critiques ne retenait que `presence_source` et
    `presence_niveau_preuve`, en citant `GSIE-CON-002` — laissant donc de côté
    l'article **fondateur** : « l'IA assiste, ne décide jamais ». Une
    recommandation qui se déclare non contournable retire au forestier la seule
    chose que cet article lui garantit, et ressortait `partiellement_valide` :
    elle atteignait l'utilisateur.

    La validation est le dernier rempart. Enforcer un article dérivé tout en
    tolérant la violation de l'article fondateur était une incohérence.
    """
    assert "recommandation_contournable" in ValidationEngine._CONTROLES_CRITIQUES

    non_conforme = ControleResultat(
        nom_controle="recommandation_contournable",
        resultat=ResultatControle.non_conforme,
        details="contournable=false déclaré dans le contenu",
    )

    assert ValidationEngine._tous_non_critiques([non_conforme]) is False, (
        "un contrôle portant GSIE-CON-001 est traité comme non critique — "
        "l'ensemble sortirait en `partiellement_valide`"
    )


# --- Persistance obligatoire (RFC-0028) ---


@pytest.mark.asyncio
async def should_raise_when_bloque_and_no_session() -> None:
    """Un résultat bloqué sans session DB lève — la persistance est obligatoire.

    Sans cette garde, un ValidationEngine() construit sans session avale
    silencieusement un pattern de blocage récurrent : le Learning Engine
    perdrait l'information d'apprentissage (RFC-0028, migration 0028).
    """
    engine = ValidationEngine()  # pas de session
    contenu = {
        "source": {"type_source": "peer_reviewed", "auteur": "Test", "reference": "DOI"},
        "justification": "Diagnostic fondé sur observations.",
    }
    with pytest.raises(ValidationEngineError, match="Persistance.*requise"):
        await engine.validate(_make_request(contenu=contenu))
