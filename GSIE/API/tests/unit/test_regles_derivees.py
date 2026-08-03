"""Dérivation d'une règle depuis un fait sourcé — RFC-0028 §4.2, DEC-000038.

La condition exécutable est dérivée, jamais stockée : une chaîne persistée
pourrait diverger du seuil qu'elle traduit. Ces tests vérifient que la
dérivation est fidèle, et surtout qu'elle **refuse** plutôt que de compléter.

Un seuil dont l'opérateur manque n'est pas « probablement inférieur à ». Il
est inutilisable, et le dire est le seul comportement acceptable (`ADR-009`).
"""

from __future__ import annotations

import pytest

from gsie_api.engines.knowledge.regles import (
    DerivationImpossibleError,
    condition_derivee,
    deriver_regle,
)

_SEUIL_COMPLET = {
    "variable": "reserve_utile_mm",
    "operateur": "<",
    "valeur": "120",
    "enonce_conclusion": "contrainte hydrique pour le chêne sessile",
    "niveau_confiance": "0.8",
}


class TestDerivationNominale:
    def test_un_seuil_complet_donne_sa_condition(self) -> None:
        regle = deriver_regle("assertion-1", _SEUIL_COMPLET)

        assert regle.condition == "reserve_utile_mm < 120"
        assert regle.enonce_conclusion == "contrainte hydrique pour le chêne sessile"
        assert regle.variable == "reserve_utile_mm"

    @pytest.mark.parametrize("operateur", ["<", "<=", ">", ">=", "==", "!="])
    def test_les_comparaisons_admises_sont_derivees(self, operateur: str) -> None:
        regle = deriver_regle("a", {**_SEUIL_COMPLET, "operateur": operateur})

        assert regle.condition == f"reserve_utile_mm {operateur} 120"

    def test_les_espaces_parasites_sont_absorbes(self) -> None:
        regle = deriver_regle(
            "a", {**_SEUIL_COMPLET, "variable": "  reserve_utile_mm  ", "valeur": " 120 "}
        )

        assert regle.condition == "reserve_utile_mm < 120"


class TestRefusPlutotQueCompletion:
    """Ce qui manque est nommé — jamais remplacé par une valeur par défaut."""

    @pytest.mark.parametrize("cle", ["variable", "operateur", "valeur", "enonce_conclusion"])
    def test_un_qualificateur_absent_refuse_la_regle(self, cle: str) -> None:
        incomplet = {k: v for k, v in _SEUIL_COMPLET.items() if k != cle}

        with pytest.raises(DerivationImpossibleError) as erreur:
            deriver_regle("assertion-2", incomplet)

        assert erreur.value.assertion_id == "assertion-2"
        assert any(cle in manque for manque in erreur.value.manques)

    def test_un_qualificateur_vide_vaut_absent(self) -> None:
        """Une chaîne vide n'est pas une valeur — c'est un champ non renseigné."""
        with pytest.raises(DerivationImpossibleError):
            deriver_regle("a", {**_SEUIL_COMPLET, "operateur": "   "})

    def test_tous_les_manques_sont_signales_ensemble(self) -> None:
        """Échouer sur le premier problème obligerait à corriger un par un."""
        with pytest.raises(DerivationImpossibleError) as erreur:
            deriver_regle("a", {"variable": "reserve_utile_mm"})

        assert len(erreur.value.manques) == 4

    def test_un_operateur_non_comparatif_est_refuse(self) -> None:
        """La surface d'exécution reste une comparaison, jamais un appel."""
        with pytest.raises(DerivationImpossibleError) as erreur:
            deriver_regle("a", {**_SEUIL_COMPLET, "operateur": "and"})

        assert "non admis" in erreur.value.manques[0]

    def test_une_valeur_non_numerique_est_refusee(self) -> None:
        with pytest.raises(DerivationImpossibleError) as erreur:
            deriver_regle("a", {**_SEUIL_COMPLET, "valeur": "faible"})

        assert "non numérique" in erreur.value.manques[0]


class TestSurfaceDExecution:
    """La condition dérivée ne doit jamais devenir un vecteur d'exécution."""

    @pytest.mark.parametrize(
        "valeur",
        ["__import__('os')", "1); import os; (1", "open('/etc/passwd')", "1 or True"],
    )
    def test_une_valeur_injectee_ne_passe_pas(self, valeur: str) -> None:
        with pytest.raises(ValueError, match="non numérique"):
            condition_derivee("reserve_utile_mm", "<", valeur)

    def test_une_valeur_negative_reste_admise(self) -> None:
        """Témoin : c'est bien le non-numérique qui est refusé, pas le signe."""
        assert condition_derivee("temperature_c", "<", "-5.5") == "temperature_c < -5.5"


class TestVocabulaireControle:
    """Le flottement des noms de variables doit être impossible, pas signalé.

    Sans référentiel commun, « RUM », « réserve utile » et `reserve_utile_mm`
    désignent la même grandeur sans qu'aucun rapprochement soit possible : la
    règle est retournée, puis échoue silencieusement parce que le fait de la
    station ne porte pas le même nom. Un échec silencieux vaut ici une absence
    de connaissance, sans que personne ne le voie.
    """

    # Correspondance code -> nom du fait dans le contexte : le contexte prefixe
    # ses faits par leur bloc d'origine.
    _VOCABULAIRE = {
        "reserve_utile_mm": "pedologie_reserve_utile_mm",
        "ph_optimal": "pedologie_ph_optimal",
        "profondeur_cm": "pedologie_profondeur_cm",
    }

    def test_une_variable_du_vocabulaire_passe(self) -> None:
        regle = deriver_regle("a", _SEUIL_COMPLET, variables_connues=self._VOCABULAIRE)

        assert regle.condition == "pedologie_reserve_utile_mm < 120"

    @pytest.mark.parametrize("ecriture", ["RUM", "reserve utile", "reserve_utile", "RU_mm"])
    def test_une_ecriture_flottante_est_refusee(self, ecriture: str) -> None:
        """Ces quatre écritures désignent la même grandeur — aucune n'est le code."""
        with pytest.raises(DerivationImpossibleError) as erreur:
            deriver_regle(
                "a",
                {**_SEUIL_COMPLET, "variable": ecriture},
                variables_connues=self._VOCABULAIRE,
            )

        assert "hors vocabulaire" in erreur.value.manques[0]
        assert ecriture in erreur.value.manques[0]

    def test_sans_vocabulaire_le_controle_est_inactif(self) -> None:
        """Témoin : c'est bien le vocabulaire qui refuse, pas la variable en soi."""
        regle = deriver_regle("a", {**_SEUIL_COMPLET, "variable": "RUM"})

        assert regle.variable == "RUM"


class TestConfianceDeclaree:
    """La confiance est déclarée, jamais déduite du niveau de preuve.

    Les deux mesurent des choses différentes : le niveau de preuve qualifie la
    **source**, la confiance dit avec quelle force la règle s'applique. Les
    convertir l'un en l'autre supposerait une table de correspondance que
    personne n'a établie — c'est ce que le Diagnostic Engine refuse
    explicitement (`ADR-009`).
    """

    def test_la_confiance_declaree_est_reprise(self) -> None:
        regle = deriver_regle("a", {**_SEUIL_COMPLET, "niveau_confiance": "0.65"})

        assert regle.niveau_confiance == 0.65

    @pytest.mark.parametrize("valeur", ["1.5", "-0.2", "beaucoup", ""])
    def test_une_confiance_hors_bornes_ou_illisible_refuse_la_regle(self, valeur: str) -> None:
        with pytest.raises(DerivationImpossibleError):
            deriver_regle("a", {**_SEUIL_COMPLET, "niveau_confiance": valeur})

    @pytest.mark.parametrize("borne", ["0", "1"])
    def test_les_bornes_restent_admises(self, borne: str) -> None:
        """Témoin : ce sont les valeurs hors [0,1] qui sont refusées."""
        regle = deriver_regle("a", {**_SEUIL_COMPLET, "niveau_confiance": borne})

        assert regle.niveau_confiance == float(borne)
