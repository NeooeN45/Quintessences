"""Tests étendus — ReasoningEngine, edge cases non couverts par test_reasoning_engine.py.

Cible les lignes manquantes identifiées par coverage :
- 140 : opérateur de comparaison interdit (ast.Is, ast.In, ast.IsNot)
- 148 : connecteur logique interdit (théoriquement impossible en Python)
- 151-155 : opérateur unaire interdit (ast.USub, ast.UAdd) + construction interdite
- 168-169 : condition non parsable (SyntaxError)
- 201-202 : bloc correlation dans le contexte
- 312-313 : ValueError (condition mal formée) remontée
- 339 : variable sans provenance traçable (edge case défensif)
- 581, 585 : _collecter_dependances avec règle inconnue / déjà visitée
- 629, 634, 638 : _detecter_contradictions avec cible inconnue / conclusion absente / doublon

Valeurs métier (ADR-009) :
- pH 4,5–6,0 — source : Rameau et al., 2018.
- Précipitations ≥ 700 mm/an — source : ONF, 2020.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import UUID

import pytest

import gsie_api.engines.reasoning.engine as _engine_module
from gsie_api.engines.evidence.schemas import (
    EvidenceLevel,
    SourceReference,
    SourceType,
)
from gsie_api.engines.reasoning.engine import (
    ReasoningEngine,
    ReasoningEngineError,
    RegleInference,
    _dependances_transitives,
    _detecter_contradictions,
    _evaluer_condition,
)
from gsie_api.engines.reasoning.schemas import (
    BlocContexte,
    Conclusion,
    EtapeInference,
    MethodeConfiance,
    ReasoningRequest,
    SourceMoteurContexte,
    StationContexte,
)

# Workaround : engine.py importe SourceReference et EvidenceLevel sous
# TYPE_CHECKING uniquement. Voir test_reasoning_engine.py pour le détail.
_engine_module.SourceReference = SourceReference  # type: ignore[attr-defined]
_engine_module.EvidenceLevel = EvidenceLevel  # type: ignore[attr-defined]
RegleInference.model_rebuild()

_REQUETE_ID = UUID("22222222-2222-4222-8222-222222222222")
_DATE_INFERENCE = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


def _source(auteur: str = "Rameau et al.") -> SourceReference:
    return SourceReference(
        type_source=SourceType.peer_reviewed,
        auteur=auteur,
        reference="doi:10.0000/test",
    )


def _bloc(
    valeurs: dict[str, float | int | str | bool],
    source_moteur: SourceMoteurContexte = SourceMoteurContexte.pedology,
) -> BlocContexte:
    return BlocContexte(
        source_moteur=source_moteur,
        source=_source(),
        evidence_level=EvidenceLevel.B,
        valeurs=valeurs,
    )


def _regle(
    identifiant: str,
    condition: str,
    enonce: str = "Conclusion test",
    contredit: str | None = None,
    evidence: EvidenceLevel = EvidenceLevel.B,
) -> RegleInference:
    return RegleInference(
        identifiant=identifiant,
        condition=condition,
        enonce_conclusion=enonce,
        source=_source(),
        evidence_level=evidence,
        niveau_confiance=0.82,
        contredit_regle_id=contredit,
    )


def _requete(
    contexte: StationContexte,
    regles: list[RegleInference],
    profondeur_max: int = 5,
) -> ReasoningRequest:
    return ReasoningRequest(
        requete_id=_REQUETE_ID,
        contexte=contexte,
        regles=regles,
        question="Question test",
        profondeur_max=profondeur_max,
    )


def _engine() -> ReasoningEngine:
    return ReasoningEngine(session=Mock())


def _etape(enonce: str = "Conclusion test") -> EtapeInference:
    """Crée une EtapeInference valide pour les tests de Conclusion."""
    return EtapeInference(
        ordre=1,
        regle_appliquee=enonce,
        source_regle=_source(),
        premisses=["x = 1 (source : Test)"],
        conclusion_locale=enonce,
        evidence_level=EvidenceLevel.B,
    )


def _conclusion(
    enonce: str = "Conclusion test",
    conclusion_id: UUID | None = None,
) -> Conclusion:
    """Crée une Conclusion valide pour les tests de _detecter_contradictions."""
    from uuid import uuid4

    return Conclusion(
        conclusion_id=conclusion_id or uuid4(),
        enonce=enonce,
        niveau_confiance=0.82,
        methode_confiance=MethodeConfiance.fournie_par_regle,
        evidence_level_plancher=EvidenceLevel.B,
        chaine_inference=[_etape(enonce)],
        sources_utilisees=[_source()],
    )


# ---------------------------------------------------------------------------
# A. Évaluateur AST — opérateurs interdits (lignes 140, 148, 151-155)
# ---------------------------------------------------------------------------


class TestEvaluateurASTInterdit:
    """Vérifie que l'évaluateur AST rejette les constructions interdites.

    Le moteur n'autorise que : Constant, Name, Compare (Eq/NotEq/Lt/LtE/Gt/GtE),
    BoolOp (And/Or), UnaryOp (Not). Tout autre nœud doit lever ValueError.
    """

    def test_compare_is_interdit(self) -> None:
        """L'opérateur `is` est interdit (ligne 140)."""
        with pytest.raises(ValueError, match="opérateur de comparaison interdit"):
            _evaluer_condition("x is None", {"x": 1})

    def test_compare_in_interdit(self) -> None:
        """L'opérateur `in` est interdit (ligne 140)."""
        with pytest.raises(ValueError, match="opérateur de comparaison interdit"):
            _evaluer_condition("x in [1, 2, 3]", {"x": 1})

    def test_compare_is_not_interdit(self) -> None:
        """L'opérateur `is not` est interdit (ligne 140)."""
        with pytest.raises(ValueError, match="opérateur de comparaison interdit"):
            _evaluer_condition("x is not None", {"x": 1})

    def test_unary_sub_interdit(self) -> None:
        """L'opérateur unaire `-` (négation arithmétique) est interdit (ligne 152)."""
        with pytest.raises(ValueError, match="opérateur unaire interdit"):
            _evaluer_condition("-x > 0", {"x": 1})

    def test_unary_add_interdit(self) -> None:
        """L'opérateur unaire `+` est interdit (ligne 152)."""
        with pytest.raises(ValueError, match="opérateur unaire interdit"):
            _evaluer_condition("+x > 0", {"x": 1})

    def test_binop_interdit(self) -> None:
        """Une opération binaire (`x + 1`) est interdite (ligne 155)."""
        with pytest.raises(ValueError, match="construction interdite"):
            _evaluer_condition("x + 1 > 0", {"x": 1})

    def test_call_interdit(self) -> None:
        """Un appel de fonction est interdit (ligne 155)."""
        with pytest.raises(ValueError, match="construction interdite"):
            _evaluer_condition("len(x) > 0", {"x": "abc"})

    def test_attribute_interdit(self) -> None:
        """Un accès d'attribut est interdit (ligne 155)."""
        with pytest.raises(ValueError, match="construction interdite"):
            _evaluer_condition("x.value > 0", {"x": 1})

    def test_if_exp_interdit(self) -> None:
        """Une expression conditionnelle ternaire est interdite (ligne 155)."""
        with pytest.raises(ValueError, match="construction interdite"):
            _evaluer_condition("1 if x else 0", {"x": True})


# ---------------------------------------------------------------------------
# B. Condition non parsable (ligne 168-169)
# ---------------------------------------------------------------------------


class TestConditionSyntaxError:
    """Vérifie qu'une condition syntaxiquement invalide lève ValueError."""

    def test_condition_parenthese_non_fermee(self) -> None:
        """Une condition avec parenthèse non fermée doit lever ValueError."""
        with pytest.raises(ValueError, match="condition non parsable"):
            _evaluer_condition("(x > 1", {"x": 2})

    def test_condition_double_operateur(self) -> None:
        """Une condition avec double opérateur (BinOp) est interdite."""
        # `x >> 1` est parsable mais BinOp est interdit
        with pytest.raises(ValueError, match="construction interdite"):
            _evaluer_condition("x >> 1", {"x": 2})

    def test_condition_vide(self) -> None:
        """Une condition vide doit lever ValueError."""
        with pytest.raises(ValueError, match="condition non parsable"):
            _evaluer_condition("", {})

    async def test_regle_condition_invalide_leve_engine_error(self) -> None:
        """Une règle avec condition invalide doit lever ReasoningEngineError (ligne 312-313)."""
        contexte = StationContexte(pedologie=_bloc({"pH": 5.0}))
        regle = _regle("R_BAD", condition="(pH > 1")
        requete = _requete(contexte, [regle])
        with pytest.raises(ReasoningEngineError, match="condition mal formée"):
            await _engine().infer(requete, date_inference=_DATE_INFERENCE)


# ---------------------------------------------------------------------------
# C. Bloc correlation dans le contexte (lignes 201-202)
# ---------------------------------------------------------------------------


class TestBlocCorrelation:
    """Vérifie que les blocs correlation du contexte sont aplatis correctement."""

    async def test_regle_utilisant_fait_correlation(self) -> None:
        """Une règle peut référencer une variable issue d'un bloc correlation."""
        bloc_corr = _bloc(
            {"coefficient_pH_presence": 0.85},
            source_moteur=SourceMoteurContexte.correlation,
        )
        contexte = StationContexte(
            pedologie=_bloc({"pH": 5.0}),
            correlations=[bloc_corr],
        )
        regle = _regle(
            "R_CORR",
            condition="correlation_coefficient_pH_presence > 0.5",
            enonce="Correlation positive entre pH et presence.",
        )
        requete = _requete(contexte, [regle])
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)
        assert len(resultat.conclusions) == 1
        assert resultat.conclusions[0].enonce == "Correlation positive entre pH et presence."

    async def test_regle_correlation_non_satisfaite(self) -> None:
        """Une règle avec condition correlation non satisfaite ne produit rien."""
        bloc_corr = _bloc(
            {"coefficient_pH_presence": 0.3},
            source_moteur=SourceMoteurContexte.correlation,
        )
        contexte = StationContexte(
            pedologie=_bloc({"pH": 5.0}),
            correlations=[bloc_corr],
        )
        regle = _regle(
            "R_CORR",
            condition="correlation_coefficient_pH_presence > 0.5",
        )
        requete = _requete(contexte, [regle])
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)
        assert len(resultat.conclusions) == 0


# ---------------------------------------------------------------------------
# D. _collecter_dependances — edge cases (lignes 581, 585)
# ---------------------------------------------------------------------------


class TestCollecterDependances:
    """Vérifie _dependances_transitives avec règle inconnue et cycles."""

    def test_regle_inconnue_retourne_ensemble_vide(self) -> None:
        """Une règle inconnue (non dans la liste) retourne un ensemble vide (ligne 585)."""
        regle = _regle("R1", "pedologie_pH > 4")
        # L'identifiant passé n'est pas dans la liste des règles
        deps = _dependances_transitives("REGLE_INCONNUE", {}, [regle], {})
        assert deps == set()

    def test_regle_sans_dependances(self) -> None:
        """Une règle qui ne référence que des faits de contexte n'a pas de dépendances."""
        regle = _regle("R1", "pedologie_pH > 4")
        deps = _dependances_transitives("R1", {}, [regle], {})
        assert deps == set()

    def test_regle_avec_dependance_circulaire(self) -> None:
        """Une dépendance circulaire ne boucle pas (déjà visité, ligne 581)."""
        r1 = _regle("R1", "conclusion_R2")
        r2 = _regle("R2", "conclusion_R1")
        # provenance_faits_derives : conclusion_R1 -> R1, conclusion_R2 -> R2
        provenance = {"conclusion_R1": "R1", "conclusion_R2": "R2"}
        deps = _dependances_transitives("R1", provenance, [r1, r2], {})
        # R1 dépend de R2, R2 dépend de R1 → cycle, mais pas de boucle infinie
        assert "R2" in deps


# ---------------------------------------------------------------------------
# E. _detecter_contradictions — edge cases (lignes 629, 634, 638)
# ---------------------------------------------------------------------------


class TestDetecterContradictions:
    """Vérifie _detecter_contradictions avec cible inconnue, conclusion absente, doublon."""

    def test_contradiction_cible_inconnue_ignoree(self) -> None:
        """Une contradiction vers une règle inconnue est ignorée (ligne 629)."""
        regle = _regle("R1", "x > 1", contredit="R_INEXISTANTE")
        conclusion = _conclusion(enonce="Conclusion R1")
        contradictions = _detecter_contradictions([regle], [conclusion])
        assert len(contradictions) == 0

    def test_contradiction_conclusion_cible_absente_ignoree(self) -> None:
        """Une contradiction où la cible n'a pas produit de conclusion est ignorée (ligne 634)."""
        r1 = _regle("R1", "x > 1", contredit="R2")
        r2 = _regle("R2", "x < 0")  # R2 ne produit pas de conclusion (condition non satisfaite)
        # Seule la conclusion de R1 est présente
        conclusion_r1 = _conclusion(enonce="Conclusion R1")
        contradictions = _detecter_contradictions([r1, r2], [conclusion_r1])
        assert len(contradictions) == 0

    def test_contradiction_doublon_non_duplique(self) -> None:
        """Si R1 contredit R2 et R2 contredit R1, une seule contradiction (ligne 638)."""
        r1 = _regle("R1", "x > 1", enonce="Conclusion R1", contredit="R2")
        r2 = _regle("R2", "x < 0", enonce="Conclusion R2", contredit="R1")
        c1 = _conclusion(enonce="Conclusion R1")
        c2 = _conclusion(enonce="Conclusion R2")
        contradictions = _detecter_contradictions([r1, r2], [c1, c2])
        assert len(contradictions) == 1

    def test_aucune_contradiction_sans_conclusions(self) -> None:
        """Sans conclusions, aucune contradiction (ligne 611-612)."""
        regle = _regle("R1", "x > 1", contredit="R2")
        contradictions = _detecter_contradictions([regle], [])
        assert contradictions == []

    def test_aucune_contradiction_sans_contredit(self) -> None:
        """Des règles sans contredit_regle_id ne produisent pas de contradiction."""
        r1 = _regle("R1", "x > 1")
        r2 = _regle("R2", "x < 0")
        c1 = _conclusion(enonce="C1")
        c2 = _conclusion(enonce="C2")
        contradictions = _detecter_contradictions([r1, r2], [c1, c2])
        assert contradictions == []


# ---------------------------------------------------------------------------
# F. Intégration — chaînage avec correlation + contradiction (lignes combinées)
# ---------------------------------------------------------------------------


class TestIntegrationChainageComplet:
    """Tests d'intégration couvrant plusieurs chemins du moteur simultanément."""

    async def test_chainage_avec_correlation_et_contradiction(self) -> None:
        """Chaîne complète : contexte + correlation + règle + contradiction déclarée."""
        bloc_corr = _bloc(
            {"coefficient_pH_presence": 0.9},
            source_moteur=SourceMoteurContexte.correlation,
        )
        contexte = StationContexte(
            pedologie=_bloc({"pH": 5.0}),
            correlations=[bloc_corr],
        )
        r1 = _regle(
            "R1",
            "pedologie_pH >= 4.5 and pedologie_pH <= 6.0",
            enonce="Le sol est acide.",
        )
        r2 = _regle(
            "R2",
            "correlation_coefficient_pH_presence > 0.5",
            enonce="Forte correlation positive pH-presence.",
            contredit="R1",
        )
        requete = _requete(contexte, [r1, r2])
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)

        # Les deux règles s'appliquent
        assert len(resultat.conclusions) == 2
        # Une contradiction est détectée (R2 contredit R1)
        assert len(resultat.contradictions) == 1
        contradiction = resultat.contradictions[0]
        assert "R1" in contradiction.description
        assert "R2" in contradiction.description

    async def test_profondeur_max_un_tronque_chainage(self) -> None:
        """Avec profondeur_max=1, un chaînage de 2 niveaux est tronqué (résultat_partiel)."""
        contexte = StationContexte(pedologie=_bloc({"pH": 5.0}))
        r1 = _regle("R1", "pedologie_pH > 4", enonce="Premier niveau.")
        r2 = _regle("R2", "conclusion_R1", enonce="Deuxieme niveau.")
        requete = _requete(contexte, [r1, r2], profondeur_max=1)
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)
        # R1 s'applique au tour 1, R2 nécessite le tour 2 qui est au-delà de la borne
        assert len(resultat.conclusions) == 1
        assert resultat.conclusions[0].enonce == "Premier niveau."
        # Le résultat est partiel : R2 n'a pas pu être appliquée
        assert resultat.resultat_partiel is True
        assert "R2" in resultat.regles_non_appliquees

    async def test_variable_conclusion_non_produite_ne_leve_pas(self) -> None:
        """Une règle citant conclusion_RX sans que RX soit appliquée ne lève pas.

        Cf. engine.py lignes 303-304.
        """
        contexte = StationContexte(pedologie=_bloc({"pH": 5.0}))
        # R1 ne s'applique pas (pH > 10 est faux)
        r1 = _regle("R1", "pedologie_pH > 10", enonce="Sol tres alcalin.")
        # R2 référence conclusion_R1 qui n'existera pas
        r2 = _regle("R2", "conclusion_R1", enonce="Conclusion dependante.")
        requete = _requete(contexte, [r1, r2])
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)
        # Aucune conclusion — R1 non satisfaite, R2 ignorée (pas d'erreur)
        assert len(resultat.conclusions) == 0

    async def test_negation_logique_authorisee(self) -> None:
        """L'opérateur `not` est autorisé (UnaryOp ast.Not)."""
        contexte = StationContexte(pedologie=_bloc({"pH": 7.5}))
        regle = _regle(
            "R_NOT",
            "not (pedologie_pH >= 4.5 and pedologie_pH <= 6.0)",
            enonce="Le sol n est pas acide.",
        )
        requete = _requete(contexte, [regle])
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)
        assert len(resultat.conclusions) == 1
        assert resultat.conclusions[0].enonce == "Le sol n est pas acide."

    async def test_disjonction_or_authorisee(self) -> None:
        """L'opérateur `or` est autorisé (BoolOp ast.Or)."""
        contexte = StationContexte(pedologie=_bloc({"pH": 3.0}))
        regle = _regle(
            "R_OR",
            "pedologie_pH < 4.0 or pedologie_pH > 8.0",
            enonce="Sol extreme.",
        )
        requete = _requete(contexte, [regle])
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)
        assert len(resultat.conclusions) == 1

    async def test_compare_egalite_authorisee(self) -> None:
        """L'opérateur `==` est autorisé (Compare ast.Eq)."""
        contexte = StationContexte(pedologie=_bloc({"pH": 5.0}))
        regle = _regle(
            "R_EQ",
            "pedologie_pH == 5.0",
            enonce="pH exactement 5.",
        )
        requete = _requete(contexte, [regle])
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)
        assert len(resultat.conclusions) == 1

    async def test_compare_inegalite_authorisee(self) -> None:
        """L'opérateur `!=` est autorisé (Compare ast.NotEq)."""
        contexte = StationContexte(pedologie=_bloc({"pH": 5.0}))
        regle = _regle(
            "R_NEQ",
            "pedologie_pH != 7.0",
            enonce="pH non neutre.",
        )
        requete = _requete(contexte, [regle])
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)
        assert len(resultat.conclusions) == 1

    async def test_chainage_compare_chainee_authorisee(self) -> None:
        """Les comparaisons chaînées (a < b < c) sont autorisées."""
        contexte = StationContexte(pedologie=_bloc({"pH": 5.0}))
        regle = _regle(
            "R_CHAIN",
            "4.0 < pedologie_pH < 6.0",
            enonce="pH dans la plage.",
        )
        requete = _requete(contexte, [regle])
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)
        assert len(resultat.conclusions) == 1
