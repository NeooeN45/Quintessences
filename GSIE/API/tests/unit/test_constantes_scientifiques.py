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


def test_les_niveaux_de_confiance_des_recommandations_sont_figes() -> None:
    """Le moteur v1 annonce une confiance déclarée : elle ne doit pas glisser.

    Ces valeurs sont lues par le forestier pour pondérer une proposition. Les
    voir changer sans décision tracée reviendrait à modifier un jugement
    au nom de quelqu'un d'autre (GSIE-CON-001).
    """
    import inspect

    from gsie_api.engines.recommendation import engine as moteur

    source = inspect.getsource(moteur)
    attendus = ["niveau_confiance=0.70", "niveau_confiance=0.60", "niveau_confiance=0.55"]

    for litteral in attendus:
        assert litteral in source, (
            f"Niveau de confiance modifié : « {litteral} » absent de "
            "recommendation/engine.py. Toute évolution doit être tracée "
            "(DEC-xxxxxx) et répercutée ici."
        )
