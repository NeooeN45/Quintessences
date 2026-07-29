"""Verrou sur les constantes scientifiques sourcées.

`GSIE-CON-005` exige que toute donnée écologique cite sa source, et la
Constitution pose que « la connaissance est le véritable produit ». Or un
audit par mutation a montré qu'on pouvait remplacer un accroissement moyen
annuel IGN par n'importe quelle valeur, ou ramener un niveau de confiance de
0,70 à 0,01, sans qu'un seul des mille tests ne tombe.

Une constante scientifique qui dérive en silence est pire qu'une absence de
donnée : elle reste citable, donc elle sera citée. Ces tests la figent.

Ils ne valident pas la science — ils garantissent que la valeur en vigueur est
bien celle qui a été documentée et sourcée. Modifier une valeur ici est
délibéré : cela impose de mettre à jour la source citée dans le même geste.
"""

from __future__ import annotations

import pytest

from gsie_api.engines.growth_models import _GROWTH_PARAMETERS

# Source : IGN — Inventaire Forestier National, résultats d'inventaire
# (production et accroissements). Valeurs documentées en tête de
# `engines/growth_models.py`.
# essence -> (AMA volume m³/ha/an, AMA circonférence cm/an, production max m³/ha)
_VALEURS_IGN: dict[str, tuple[float, float, float]] = {
    "Quercus petraea": (5.0, 1.5, 400.0),
    "Quercus robur": (5.5, 1.5, 400.0),
    "Fagus sylvatica": (7.0, 2.0, 500.0),
    "Pinus sylvestris": (6.0, 2.5, 350.0),
    "Quercus ilex": (2.0, 0.8, 150.0),
    "Abies alba": (9.0, 2.5, 600.0),
}


def test_le_corpus_des_essences_calibrees_est_complet() -> None:
    """Retirer une essence calibrée doit être un acte visible."""
    assert set(_GROWTH_PARAMETERS) == set(_VALEURS_IGN)


@pytest.mark.parametrize(("essence", "attendu"), sorted(_VALEURS_IGN.items()))
def test_les_accroissements_ign_sont_ceux_documentes(
    essence: str, attendu: tuple[float, float, float]
) -> None:
    parametres = _GROWTH_PARAMETERS[essence]
    constate = (
        parametres.accroissement_moyen_annuel_volume,
        parametres.accroissement_moyen_annuel_circonference,
        parametres.production_maximale_volume,
    )

    assert constate == attendu, (
        f"Constante de croissance modifiée pour {essence} : {constate} au lieu "
        f"de {attendu}. Si le changement est voulu, mettre à jour la source IGN "
        f"citée dans engines/growth_models.py et ce verrou dans le même commit."
    )


@pytest.mark.parametrize("essence", sorted(_VALEURS_IGN))
def test_chaque_essence_cite_sa_source(essence: str) -> None:
    """Une valeur sans source citée n'a pas sa place dans le moteur (CON-005)."""
    source = _GROWTH_PARAMETERS[essence].source

    assert source.reference, f"{essence} : référence de source vide"
    assert "IGN" in source.auteur or "IGN" in source.reference


def test_aucune_confiance_codee_en_dur_dans_les_recommandations() -> None:
    """La confiance d'une recommandation est celle du diagnostic, jamais un littéral.

    Le moteur portait quatre constantes — 0,70 / 0,60 / 0,55 / 0,50 — sans
    lire le diagnostic qu'il invoquait. Un `diagnostic_id` inexistant produisait
    donc un conseil sylvicole complet, assorti d'une confiance inventée, citant
    une référence vide.

    Une recommandation ne peut pas être plus assurée que le diagnostic sur
    lequel elle repose. Ce verrou interdit le retour d'un nombre propre au
    moteur — c'est la règle que le Diagnostic Engine énonce déjà : « le moteur
    n'invente aucune table de conversion » (`ADR-009`).

    La source est lue via `module.__file__`, jamais par un chemin relatif : le
    harnais de mutation copie l'arborescence dans un dossier temporaire et
    pointe `PYTHONPATH` dessus. Un chemin en dur lirait le fichier intact du
    dépôt — le verrou passerait quelle que soit la mutation, et ne
    verrouillerait donc rien.
    """
    import re
    from pathlib import Path

    from gsie_api.engines.recommendation import engine as module_moteur

    assert module_moteur.__file__ is not None
    source = Path(module_moteur.__file__).read_text(encoding="utf-8")
    litteraux = re.findall(r"niveau_confiance\s*=\s*([0-9.]+)", source)

    assert litteraux == [], (
        f"confiance(s) codée(s) en dur : {litteraux}. La valeur doit venir du "
        "diagnostic lu, jamais du moteur."
    )
