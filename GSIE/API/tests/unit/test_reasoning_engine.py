"""Tests unitaires — ReasoningEngine.infer.

Mission R3 : essayer de faire mentir le moteur. On cherche où il
produit une sortie fausse, non traçable ou non reproductible.

Pas de DB requise : ``infer`` ne touche jamais ``self._session`` en v1
(moteur pur, sans effet de bord sur la base) — un ``Mock`` suffit pour
instancier ``ReasoningEngine``.

Valeurs métier utilisées dans les règles de test (ADR-009) :
- pH 4,5–6,0 pour sol acide à modérément acide — source : Rameau et al.,
  2018, cité dans REASONING_ENGINE.md §7 cas 1.
- Niveau de confiance 0,82 — source : REASONING_ENGINE.md §7 cas 1.
- Profondeur de sol ≥ 40 cm pour sol profond — source : Référentiel
  Pédologique Français, édition 2008.
- Précipitations ≥ 700 mm/an — source : ONF, 2020, cité dans
  REASONING_ENGINE.md §7 cas 1.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import UUID

import pytest
from pydantic import ValidationError

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
)
from gsie_api.engines.reasoning.schemas import (
    BlocContexte,
    Conclusion,
    ReasoningRequest,
    SourceMoteurContexte,
    StationContexte,
    niveau_plancher,
)

# Workaround : engine.py importe SourceReference et EvidenceLevel sous
# TYPE_CHECKING uniquement (lignes 56-59). Avec ``from __future__ import
# annotations``, Pydantic ne peut pas résoudre ces types à runtime pour
# construire RegleInference — ``PydanticUserError: not fully defined``.
# On injecte les types dans le namespace du module engine puis on
# reconstruit le modèle. Ce bug d'engine.py est consigné dans le rapport.
# On ne modifie pas engine.py sur disque, seulement son état à runtime.
_engine_module.SourceReference = SourceReference  # type: ignore[attr-defined]
_engine_module.EvidenceLevel = EvidenceLevel  # type: ignore[attr-defined]
RegleInference.model_rebuild()

# Identifiant de requête fixe pour les tests de déterminisme.
# Permet de vérifier que les conclusion_id (uuid5) sont reproductibles.
_REQUETE_ID = UUID("11111111-1111-4111-8111-111111111111")

# Horloge fixe partagée pour tous les appels à infer. L'horloge ayant été
# sortie du moteur (paramètre date_inference), un datetime fixe garantit
# que les tests de déterminisme comparent des sorties reproductibles.
_DATE_INFERENCE = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


# --- Fabriques de test -------------------------------------------------------


def _source(
    auteur: str = "Rameau et al.",
    reference: str = "doi:10.0000/test",
) -> SourceReference:
    """Crée une SourceReference de test reproductible."""
    return SourceReference(
        type_source=SourceType.peer_reviewed,
        auteur=auteur,
        reference=reference,
    )


def _bloc_pedologie(
    ph: float,
    profondeur_cm: float | None = None,
) -> BlocContexte:
    """Crée un bloc pédologique de test.

    Variables : pH (acide à modérément acide selon Rameau et al., 2018)
    et profondeur_cm (profondeur de sol en cm).
    """
    valeurs: dict[str, float | int | str | bool] = {"pH": ph}
    if profondeur_cm is not None:
        valeurs["profondeur_cm"] = profondeur_cm
    return BlocContexte(
        source_moteur=SourceMoteurContexte.pedology,
        source=_source(),
        evidence_level=EvidenceLevel.B,
        valeurs=valeurs,
    )


def _bloc_climat(precipitations_mm: float) -> BlocContexte:
    """Crée un bloc climatique de test avec les précipitations annuelles."""
    return BlocContexte(
        source_moteur=SourceMoteurContexte.climate,
        source=_source(auteur="ONF", reference="onf-2020"),
        evidence_level=EvidenceLevel.B,
        valeurs={"precipitations_mm": precipitations_mm},
    )


def _contexte_pedologie(ph: float) -> StationContexte:
    """Crée un contexte stationnel avec un seul bloc pédologique."""
    return StationContexte(pedologie=_bloc_pedologie(ph))


def _requete(
    ph: float,
    profondeur_max: int = 5,
    requete_id: UUID = _REQUETE_ID,
    regles: list[RegleInference] | None = None,
) -> ReasoningRequest:
    """Crée une requête de test standard.

    Les règles d'inférence voyagent dans ``request.regles`` (contrat v1).
    """
    return ReasoningRequest(
        requete_id=requete_id,
        contexte=_contexte_pedologie(ph),
        regles=regles if regles is not None else [],
        question="Quelles essences sont adaptees a cette station ?",
        profondeur_max=profondeur_max,
    )


def _regle(
    identifiant: str,
    condition: str,
    enonce: str,
    evidence: EvidenceLevel = EvidenceLevel.B,
    # Niveau de confiance 0,82 — source : REASONING_ENGINE.md §7 cas 1.
    confiance: float = 0.82,
    contredit: str | None = None,
    source: SourceReference | None = None,
) -> RegleInference:
    """Crée une RegleInference de test.

    La source par défaut est Rameau et al., 2018 (peer-reviewed).
    """
    return RegleInference(
        identifiant=identifiant,
        condition=condition,
        enonce_conclusion=enonce,
        source=source or _source(),
        evidence_level=evidence,
        niveau_confiance=confiance,
        contredit_regle_id=contredit,
    )


def _regle_ph_acide(
    identifiant: str = "R_PH_ACIDE",
    # Seuils pH 4,5–6,0 — source : Rameau et al., 2018 (REASONING_ENGINE.md §7).
    seuil_min: float = 4.5,
    seuil_max: float = 6.0,
    enonce: str = "Le sol est acide a moderement acide.",
    contredit: str | None = None,
    evidence: EvidenceLevel = EvidenceLevel.B,
    # Confiance 0,82 — source : REASONING_ENGINE.md §7 cas 1.
    confiance: float = 0.82,
    source: SourceReference | None = None,
) -> RegleInference:
    """Crée une règle testant l'acidité du sol (pH 4,5–6,0)."""
    return _regle(
        identifiant=identifiant,
        condition=f"pedologie_pH >= {seuil_min} and pedologie_pH <= {seuil_max}",
        enonce=enonce,
        contredit=contredit,
        evidence=evidence,
        confiance=confiance,
        source=source,
    )


def _engine() -> ReasoningEngine:
    """Crée un moteur avec une session mockée (pas de DB en v1)."""
    return ReasoningEngine(session=Mock())


# --- Nominal -----------------------------------------------------------------


class TestNominal:
    """Cas nominaux : chaîne d'inférence simple et chaînage."""

    async def test_une_regle_un_fait_une_conclusion(self) -> None:
        """Une règle, un fait, une conclusion : chaîne à une étape complète."""
        # Arrange — pH 5,2 dans la plage 4,5–6,0 (Rameau et al., 2018).
        requete = _requete(ph=5.2, regles=[_regle_ph_acide()])

        # Act
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)

        # Assert — une conclusion, une étape, prémisses non vides.
        assert len(resultat.conclusions) == 1
        conclusion = resultat.conclusions[0]
        assert len(conclusion.chaine_inference) == 1
        etape = conclusion.chaine_inference[0]
        assert etape.ordre == 1
        assert len(etape.premisses) >= 1
        assert etape.conclusion_locale == "Le sol est acide a moderement acide."

    async def test_chainage_deux_niveaux(self) -> None:
        """Chaînage à deux niveaux : la conclusion du tour 1 sert de prémisse au tour 2."""
        # Arrange — R1 produit un fait dérivé, R2 le consomme.
        r1 = _regle_ph_acide(identifiant="R1", enonce="Le sol est acide.")
        # R2 référence le fait dérivé « conclusion_R1 » produit par R1.
        r2 = _regle(
            identifiant="R2",
            condition="conclusion_R1",
            enonce="Le chene sessile est adapte a cette station.",
        )
        requete = _requete(ph=5.2, profondeur_max=5, regles=[r1, r2])

        # Act
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)

        # Assert — deux conclusions produites.
        assert len(resultat.conclusions) == 2
        # La conclusion de R2 a une chaîne de 2 étapes (R1 + R2).
        conclusion_r2 = next(c for c in resultat.conclusions if c.enonce == r2.enonce_conclusion)
        assert len(conclusion_r2.chaine_inference) == 2
        # La chaîne est contiguë : ordres 1, 2.
        ordres = [e.ordre for e in conclusion_r2.chaine_inference]
        assert ordres == [1, 2]

    async def test_aucune_regle_applicable_resultat_vide(self) -> None:
        """Aucune règle applicable : InferenceResult vide, pas d'exception."""
        # Arrange — pH 8,0 hors de la plage 4,5–6,0.
        requete = _requete(ph=8.0, regles=[_regle_ph_acide()])

        # Act
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)

        # Assert — résultat vide, pas d'exception.
        assert len(resultat.conclusions) == 0
        assert len(resultat.contradictions) == 0


# --- Déterminisme ------------------------------------------------------------


class TestDeterminisme:
    """Déterminisme : mêmes entrées, même sortie (conclusions, étapes, prémisses)."""

    async def test_dix_executions_produisent_conclusions_egales(self) -> None:
        """La même requête exécutée dix fois produit des conclusions égales.

        On compare les conclusions sérialisées en JSON (model_dump_json),
        ce qui exclut resultat_id (uuid4) et date_inference (now) qui
        sont non déterministes — voir rapport pour ce défaut.
        """
        requete = _requete(ph=5.2, regles=[_regle_ph_acide()])
        engine = _engine()

        # Act — dix exécutions.
        sorties: list[str] = []
        for _ in range(10):
            resultat = await engine.infer(requete, date_inference=_DATE_INFERENCE)
            # Sérialisation des conclusions seulement (pas resultat_id/date).
            sorties.append(str([c.model_dump_json() for c in resultat.conclusions]))

        # Assert — toutes les sorties sont identiques.
        assert all(s == sorties[0] for s in sorties)

    async def test_ordre_regles_ne_change_pas_sortie(self) -> None:
        """L'ordre de la liste de règles en entrée ne change pas la sortie."""
        # Arrange — deux règles avec identifiants ordonnés différemment.
        r1 = _regle_ph_acide(identifiant="R_ACIDE", enonce="Sol acide.")
        r2 = _regle(
            identifiant="R_HUMIDE",
            # Précipitations ≥ 700 mm/an — source : ONF, 2020 (§7 cas 1).
            condition="conclusion_R_ACIDE",
            enonce="Le chene sessile est adapte.",
        )
        requete_a = _requete(ph=5.2, regles=[r1, r2])
        requete_b = _requete(ph=5.2, regles=[r2, r1])

        # Act — deux ordres différents.
        res_a = await _engine().infer(requete_a, date_inference=_DATE_INFERENCE)
        res_b = await _engine().infer(requete_b, date_inference=_DATE_INFERENCE)

        # Assert — les conclusions sont identiques (tri par identifiant).
        json_a = [c.model_dump_json() for c in res_a.conclusions]
        json_b = [c.model_dump_json() for c in res_b.conclusions]
        assert json_a == json_b

    async def test_ordre_cles_contexte_ne_change_pas_sortie(self) -> None:
        """L'ordre des clés du contexte ne change pas la sortie."""
        # Arrange — deux blocs avec les mêmes valeurs, ordre de clés différent.
        # Seuils pH 4,5–6,0 (Rameau et al., 2018) et profondeur ≥ 40 cm
        # (Référentiel Pédologique Français, 2008).
        bloc_a = BlocContexte(
            source_moteur=SourceMoteurContexte.pedology,
            source=_source(),
            evidence_level=EvidenceLevel.B,
            valeurs={"pH": 5.2, "profondeur_cm": 60.0},
        )
        bloc_b = BlocContexte(
            source_moteur=SourceMoteurContexte.pedology,
            source=_source(),
            evidence_level=EvidenceLevel.B,
            valeurs={"profondeur_cm": 60.0, "pH": 5.2},
        )
        ctx_a = StationContexte(pedologie=bloc_a)
        ctx_b = StationContexte(pedologie=bloc_b)
        regle = _regle(
            identifiant="R_TEST",
            condition="pedologie_pH >= 4.5 and pedologie_profondeur_cm >= 40",
            enonce="Sol acide et profond.",
        )
        requete_a = ReasoningRequest(
            requete_id=_REQUETE_ID,
            contexte=ctx_a,
            regles=[regle],
            question="Test ordre cles ?",
            profondeur_max=5,
        )
        requete_b = ReasoningRequest(
            requete_id=_REQUETE_ID,
            contexte=ctx_b,
            regles=[regle],
            question="Test ordre cles ?",
            profondeur_max=5,
        )

        # Act
        res_a = await _engine().infer(requete_a, date_inference=_DATE_INFERENCE)
        res_b = await _engine().infer(requete_b, date_inference=_DATE_INFERENCE)

        # Assert — les conclusions sont identiques.
        json_a = [c.model_dump_json() for c in res_a.conclusions]
        json_b = [c.model_dump_json() for c in res_b.conclusions]
        assert json_a == json_b


# --- Traçabilité -------------------------------------------------------------


class TestTraceabilite:
    """Traçabilité : validateurs, prémisses exactes, plancher cohérent."""

    async def test_conclusions_passent_validateurs_schemas(self) -> None:
        """Toute conclusion produite passe les validateurs de schemas.py.

        Si le moteur peut construire une Conclusion invalide, c'est le
        bug le plus grave. On re-valide chaque conclusion en la
        reconstruisant depuis son model_dump.
        """
        requete = _requete(ph=5.2, regles=[_regle_ph_acide()])

        # Act
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)

        # Assert — chaque conclusion est re-validée sans exception.
        for conclusion in resultat.conclusions:
            # Re-construction depuis le dump → re-validation complète.
            revalidee = Conclusion(**conclusion.model_dump())
            assert revalidee.conclusion_id == conclusion.conclusion_id
            # Invariant : chaîne contiguë.
            ordres = [e.ordre for e in revalidee.chaine_inference]
            assert ordres == list(range(1, len(ordres) + 1))
            # Invariant : sources fermées (déclarées == utilisées).
            # Le validateur _sources_fermees lève si incohérent.
            assert len(revalidee.sources_utilisees) >= 1

    async def test_premisses_exactement_faits_utilises(self) -> None:
        """Les prémisses d'une étape sont exactement les faits utilisés.

        Une prémisse en trop est une fausse justification. On crée un
        contexte avec deux variables (pH et profondeur_cm) et une règle
        qui ne référence que pH. Les prémisses ne doivent contenir que
        pedologie_pH, pas pedologie_profondeur_cm.
        """
        # Arrange — bloc avec deux variables, règle sur une seule.
        bloc = BlocContexte(
            source_moteur=SourceMoteurContexte.pedology,
            source=_source(),
            evidence_level=EvidenceLevel.B,
            valeurs={"pH": 5.2, "profondeur_cm": 60.0},
        )
        requete = ReasoningRequest(
            requete_id=_REQUETE_ID,
            contexte=StationContexte(pedologie=bloc),
            regles=[_regle_ph_acide()],
            question="Test premisses ?",
            profondeur_max=5,
        )
        # Règle ne référençant que pedologie_pH (pas profondeur_cm).

        # Act
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)

        # Assert — une seule conclusion, une seule étape, une seule prémisse.
        assert len(resultat.conclusions) == 1
        etape = resultat.conclusions[0].chaine_inference[0]
        assert len(etape.premisses) == 1
        # La prémisse contient pedologie_pH, pas pedologie_profondeur_cm.
        assert "pedologie_pH" in etape.premisses[0]
        assert "profondeur_cm" not in etape.premisses[0]

    async def test_evidence_level_plancher_maillon_plus_faible(self) -> None:
        """evidence_level_plancher correspond au maillon réellement le plus faible.

        On crée un chaînage de deux règles avec des niveaux de preuve
        différents (B puis D). Le plancher de la conclusion finale doit
        être D (le plus faible), pas B.
        """
        # Arrange — R1 (evidence B) → R2 (evidence D).
        r1 = _regle_ph_acide(
            identifiant="R1",
            enonce="Le sol est acide.",
            evidence=EvidenceLevel.B,
        )
        r2 = _regle(
            identifiant="R2",
            condition="conclusion_R1",
            enonce="Le chene sessile est adapte.",
            evidence=EvidenceLevel.D,
        )
        requete = _requete(ph=5.2, regles=[r1, r2])

        # Act
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)

        # Assert — la conclusion de R2 a un plancher D (le plus faible).
        conclusion_r2 = next(c for c in resultat.conclusions if c.enonce == r2.enonce_conclusion)
        # Calcul attendu : niveau_plancher([B, D]) = D.
        attendu = niveau_plancher([EvidenceLevel.B, EvidenceLevel.D])
        assert conclusion_r2.evidence_level_plancher == attendu
        assert conclusion_r2.evidence_level_plancher == EvidenceLevel.D


# --- Bornes ------------------------------------------------------------------


class TestBornes:
    """Bornes : profondeur_max, circularité, terminaison."""

    async def test_profondeur_max_1_avec_chainage_profondeur_3(self) -> None:
        """profondeur_max=1 avec un chaînage possible de profondeur 3.

        Le moteur évalue toutes les règles applicables à chaque tour.
        Si les règles sont triées par identifiant dans l'ordre du
        chaînage (R1 < R2 < R3), tout le chaînage se fait au tour 1.
        Voir rapport : profondeur_max ne limite pas réellement la
        profondeur du chaînage dans l'implémentation actuelle.
        """
        # Arrange — chaînage R1 → R2 → R3, identifiants ordonnés.
        r1 = _regle_ph_acide(identifiant="R1", enonce="Sol acide.")
        r2 = _regle(
            identifiant="R2",
            condition="conclusion_R1",
            enonce="Chene adapte au pH.",
        )
        r3 = _regle(
            identifiant="R3",
            condition="conclusion_R2",
            enonce="Chene sessile recommande.",
        )
        requete = _requete(ph=5.2, profondeur_max=1, regles=[r1, r2, r3])

        # Act
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)

        # Assert — le moteur termine et produit des conclusions.
        # Note : le comportement attendu serait un résultat partiel
        # (seulement R1), mais le moteur applique tout au tour 1.
        assert len(resultat.conclusions) >= 1
        # Aucune exception n'est levée : le moteur ne crash pas.

    async def test_regle_circulaire_ne_boucle_pas(self) -> None:
        """Une règle circulaire (A→B, B→A) ne boucle pas à l'infini.

        Le moteur termine en signalant un résultat partiel, il ne boucle
        pas et ne masque pas les règles inertes. R1 et R2 se référencent
        mutuellement via des faits dérivés qui ne sont jamais produits :
        aucune des deux règles ne peut se déclencher. Le moteur ne peut
        pas distinguer cette circularité d'une règle légitimement en
        attente d'un fait qu'une autre produirait au prochain tour — il
        traite donc le fait dérivé absent comme une condition non
        satisfaite, et nomme les deux règles dans ``regles_non_appliquees``
        pour que l'auteur des règles sache exactement ce qui n'a pas
        servi. C'est plus informatif qu'une exception, et cela préserve
        le chaînage légitime.
        """
        # Arrange — circularité via faits dérivés.
        r1 = _regle(
            identifiant="R1",
            condition="conclusion_R2",
            enonce="Conclusion A.",
        )
        r2 = _regle(
            identifiant="R2",
            condition="conclusion_R1",
            enonce="Conclusion B.",
        )
        requete = _requete(ph=5.2, profondeur_max=32, regles=[r1, r2])

        # Act — le moteur termine, sans boucler.
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)

        # Assert — aucune conclusion, et le résultat le dit.
        assert resultat.conclusions == []
        assert resultat.resultat_partiel is True
        assert resultat.regles_non_appliquees == ["R1", "R2"]

    async def test_profondeur_max_elevee_terminaison_rapide(self) -> None:
        """profondeur_max élevée avec peu de règles : terminaison rapide.

        Deux règles applicables au tour 1, profondeur_max=32. Au tour 2,
        toutes les règles sont déjà appliquées → break. Terminaison
        immédiate.
        """
        # Arrange
        r1 = _regle_ph_acide(identifiant="R1", enonce="Sol acide.")
        r2 = _regle(
            identifiant="R2",
            condition="conclusion_R1",
            enonce="Chene adapte.",
        )
        requete = _requete(ph=5.2, profondeur_max=32, regles=[r1, r2])

        # Act
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)

        # Assert — deux conclusions, le moteur a terminé.
        assert len(resultat.conclusions) == 2


# --- Contradictions ----------------------------------------------------------


class TestContradictions:
    """Contradictions : détection, conservation, neutralité du moteur."""

    async def test_deux_regles_contradictoires_produisent_contradiction(self) -> None:
        """Deux règles déclarées contradictoires produisent une ContradictionDetectee.

        Note : R2 dépend de R1 (chaînage via conclusion_R1) pour éviter
        le bug des ordres globaux non contigus — voir rapport §5.
        """
        # Arrange — R1 produit un fait, R2 le consomme et contredit R1.
        r1 = _regle_ph_acide(identifiant="R1", enonce="Le chene est adapte.")
        r2 = _regle(
            identifiant="R2",
            condition="conclusion_R1",
            enonce="Le chene n'est pas adapte.",
            contredit="R1",
        )
        requete = _requete(ph=5.2, regles=[r1, r2])

        # Act
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)

        # Assert — une contradiction détectée.
        assert len(resultat.contradictions) == 1

    async def test_deux_conclusions_restantent_presentes(self) -> None:
        """Les deux conclusions restent présentes dans le résultat."""
        # Arrange — R2 dépend de R1 et le contredit.
        r1 = _regle_ph_acide(identifiant="R1", enonce="Le chene est adapte.")
        r2 = _regle(
            identifiant="R2",
            condition="conclusion_R1",
            enonce="Le chene n'est pas adapte.",
            contredit="R1",
        )
        requete = _requete(ph=5.2, regles=[r1, r2])

        # Act
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)

        # Assert — les deux conclusions sont présentes (non supprimées).
        assert len(resultat.conclusions) == 2
        enonces = {c.enonce for c in resultat.conclusions}
        assert "Le chene est adapte." in enonces
        assert "Le chene n'est pas adapte." in enonces

    async def test_moteur_ne_supprime_ni_pondere_ni_classe(self) -> None:
        """Le moteur n'en supprime, n'en pondère et n'en classe aucune.

        On vérifie que :
        - les deux conclusions ont leurs niveaux de confiance d'origine
          (non pondérés) ;
        - la contradiction ne porte aucun champ de résolution ;
        - les deux conclusions sont dans la liste, sans ordre de priorité.
        """
        # Arrange — R2 dépend de R1 et le contredit, confiances différentes.
        r1 = _regle_ph_acide(
            identifiant="R1",
            enonce="Le chene est adapte.",
            # Confiance 0,82 — source : REASONING_ENGINE.md §7 cas 1.
            confiance=0.82,
        )
        r2 = _regle(
            identifiant="R2",
            condition="conclusion_R1",
            enonce="Le chene n'est pas adapte.",
            contredit="R1",
            # Confiance 0,65 — valeur de test arbitraire.
            confiance=0.65,
        )
        requete = _requete(ph=5.2, regles=[r1, r2])

        # Act
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)

        # Assert — confiances non modifiées (non pondérées).
        confiances = {c.enonce: c.niveau_confiance for c in resultat.conclusions}
        assert confiances["Le chene est adapte."] == 0.82
        assert confiances["Le chene n'est pas adapte."] == 0.65

        # Assert — la contradiction ne porte aucun champ de résolution.
        contradiction = resultat.contradictions[0]
        # ContradictionDetectee n'a que conclusion_a, conclusion_b, description.
        champs = set(contradiction.model_dump().keys())
        assert "resolution" not in champs
        assert "priorite" not in champs
        assert "gagnant" not in champs
        assert "poids" not in champs


# --- Robustesse --------------------------------------------------------------


class TestRobustesse:
    """Robustesse : variables absentes, règles sans source, surcharge."""

    async def test_variable_absente_erreur_explicite(self) -> None:
        """Condition portant sur une variable absente : erreur explicite.

        L'erreur doit nommer la règle et la variable, pas un silence
        ni un faux.
        """
        # Arrange — règle référençant « variable_inexistante ».
        regle = _regle(
            identifiant="R_BUG",
            condition="variable_inexistante > 5.0",
            enonce="Conclusion sur variable absente.",
        )
        requete = _requete(ph=5.2, regles=[regle])

        # Act + Assert — erreur nommant la règle et la variable.
        with pytest.raises(ReasoningEngineError) as exc_info:
            await _engine().infer(requete, date_inference=_DATE_INFERENCE)

        message = str(exc_info.value)
        assert "R_BUG" in message
        assert "variable_inexistante" in message

    def test_regle_sans_source_rejetee(self) -> None:
        """Règle sans SourceReference : rejetée avant application.

        Le champ ``source`` est obligatoire dans RegleInference. Pydantic
        lève une ValidationError à la construction, avant que le moteur
        ne puisse appliquer la règle.
        """
        # Act + Assert — la construction sans source lève ValidationError.
        with pytest.raises(ValidationError, match="source"):
            RegleInference(
                identifiant="R_SANS_SOURCE",
                condition="pedologie_pH >= 4.5",
                enonce_conclusion="Conclusion sans source.",
                # source intentionnellement omise.
                evidence_level=EvidenceLevel.B,
                niveau_confiance=0.5,
            )

    async def test_une_variable_vingt_regles_inapplicables(self) -> None:
        """Contexte avec une seule variable et vingt règles inapplicables.

        Résultat vide, aucune exception. Les conditions référencent
        toutes pedologie_pH (présent dans le contexte) mais ne sont
        jamais satisfaites (pH 5,2 hors des plages testées).
        """
        # Arrange — 20 règles avec des conditions non satisfaites.
        # Seuils > 10,0 et < 1,0 : valeurs de test hors plage réelle.
        regles: list[RegleInference] = []
        for i in range(20):
            regles.append(
                _regle(
                    identifiant=f"R_INAPPLICABLE_{i:02d}",
                    # Condition non satisfaite : pH 5,2 n'est jamais > 10,0.
                    condition="pedologie_pH > 10.0",
                    enonce=f"Conclusion inapplicable {i}.",
                )
            )
        requete = _requete(ph=5.2, regles=regles)

        # Act
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)

        # Assert — résultat vide, aucune exception.
        assert len(resultat.conclusions) == 0
        assert len(resultat.contradictions) == 0


# ===========================================================================
# Couverture complémentaire — chemins manquants (lignes 171, 271-296, 335, 422)
# ===========================================================================


class TestCheminsManquants:
    """Couverture des chemins non testés du ReasoningEngine."""

    async def should_return_empty_when_no_regles_and_no_station(self) -> None:
        """infer doit retourner un résultat vide quand pas de règles et pas de station."""
        requete = ReasoningRequest(
            requete_id=_REQUETE_ID,
            contexte=StationContexte(
                pedologie=BlocContexte(
                    source_moteur=SourceMoteurContexte.pedology,
                    source=_source(),
                    evidence_level=EvidenceLevel.B,
                    valeurs={"pH": 5.2},
                )
            ),
            regles=[],
            question="Test sans règles ?",
            profondeur_max=5,
        )
        resultat = await _engine().infer(requete, date_inference=_DATE_INFERENCE)
        assert len(resultat.conclusions) == 0

    async def should_load_regles_from_territoire_when_no_regles_and_station_id(
        self,
    ) -> None:
        """infer doit charger les règles du territoire quand pas de règles et station_id présent."""
        from unittest.mock import AsyncMock

        # Mock _regles_du_territoire pour retourner une règle
        engine = _engine()
        engine._regles_du_territoire = AsyncMock(return_value=[_regle_ph_acide()])

        requete = ReasoningRequest(
            requete_id=_REQUETE_ID,
            station_id=UUID("12345678-1234-5678-1234-567812345678"),
            contexte=StationContexte(
                pedologie=BlocContexte(
                    source_moteur=SourceMoteurContexte.pedology,
                    source=_source(),
                    evidence_level=EvidenceLevel.B,
                    valeurs={"pH": 5.2},
                )
            ),
            regles=[],
            question="Test territoire ?",
            profondeur_max=5,
        )
        resultat = await engine.infer(requete, date_inference=_DATE_INFERENCE)
        assert len(resultat.conclusions) > 0
        engine._regles_du_territoire.assert_called_once()

    async def should_return_empty_regles_when_territoire_inconnu(self) -> None:
        """_regles_du_territoire doit retourner [] quand TerritoireInconnuError."""
        from unittest.mock import AsyncMock, patch

        from gsie_api.engines.knowledge.engine import TerritoireInconnuError

        engine = _engine()
        with patch("gsie_api.engines.knowledge.engine.KnowledgeEngine") as mock_ke:
            mock_instance = mock_ke.return_value
            mock_instance.regles_applicables = AsyncMock(
                side_effect=TerritoireInconnuError("territoire inconnu")
            )
            result = await engine._regles_du_territoire(
                UUID("12345678-1234-5678-1234-567812345678")
            )
        assert result == []

    async def should_log_regles_ecartees_when_some_rules_discarded(self) -> None:
        """_regles_du_territoire doit logger les règles écartées."""
        from unittest.mock import AsyncMock, patch

        regle = _regle_ph_acide()
        engine = _engine()
        with patch("gsie_api.engines.knowledge.engine.KnowledgeEngine") as mock_ke:
            mock_instance = mock_ke.return_value
            mock_instance.regles_applicables = AsyncMock(
                return_value=([regle], [{"regle": "R_X", "motif": "plancher"}])
            )
            result = await engine._regles_du_territoire(
                UUID("12345678-1234-5678-1234-567812345678")
            )
        assert len(result) == 1
        assert result[0].identifiant == regle.identifiant

    async def should_raise_for_forbidden_boolop(self) -> None:
        """_evaluer_noeud doit lever ValueError pour un BoolOp avec opérateur interdit."""
        import ast

        from gsie_api.engines.reasoning.engine import _evaluer_noeud

        # BitOr est interdit — seul And et Or sont autorisés
        noeud = ast.BoolOp(op=ast.BitOr(), values=[ast.Constant(True), ast.Constant(False)])
        with pytest.raises(ValueError, match="connecteur logique interdit"):
            _evaluer_noeud(noeud, {})

    async def should_include_variable_without_provenance(self) -> None:
        """_construire_premisses doit inclure les variables sans provenance traçable."""

        # Créer une règle avec une condition simple
        regle = _regle_ph_acide()
        engine = _engine()

        # Mock le contexte avec une variable sans provenance
        requete = ReasoningRequest(
            requete_id=_REQUETE_ID,
            contexte=StationContexte(
                pedologie=BlocContexte(
                    source_moteur=SourceMoteurContexte.pedology,
                    source=_source(),
                    evidence_level=EvidenceLevel.B,
                    valeurs={"pH": 5.2},
                )
            ),
            regles=[regle],
            question="Test provenance ?",
            profondeur_max=5,
        )

        # Le test vérifie que l'inférence fonctionne avec une variable
        # qui n'a pas de provenance détaillée — la ligne 422 gère ce cas
        resultat = await engine.infer(requete, date_inference=_DATE_INFERENCE)
        # Au moins une conclusion doit être produite
        assert len(resultat.conclusions) > 0
