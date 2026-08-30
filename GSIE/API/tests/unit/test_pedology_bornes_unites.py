"""Une valeur pédologique reste dans ce que son unité autorise.

Seconde ligne de défense, indépendante du client qui produit la valeur.
Le client historique `soilgrids_client.py` retombait sur un facteur d'échelle de 1 quand SoilGrids
omettait `unit_measure` : une couche `phh2o` de moyenne 52 — un pH de 5,2 mis à
l'échelle par dix — ressortait à **pH 52**, et la règle `pedologie_pH < 5.5`
évaluait alors `52 < 5.5`, diagnostiquant basique un sol acide.

Ce contrôle-ci l'arrête quel que soit le client fautif. Deux gardes valent
mieux qu'une quand la conséquence est un diagnostic inversé sans erreur levée.

**Bornes définitionnelles uniquement.** Un pourcentage supérieur à cent n'est
pas une teneur remarquable, c'est une part dépassant le tout. Aucune borne n'est
posée sur ce qui relèverait d'un jugement : dire qu'un sol est « trop acide »
exigerait une source et n'appartient pas à un schéma (`ADR-009`).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from gsie_api.engines.evidence.schemas import SourceReference, SourceType
from gsie_api.engines.pedology.schemas import SolCaracteristique

_SOURCE = SourceReference(
    type_source=SourceType.peer_reviewed,
    auteur="Poggio, L. et al. (2021)",
    reference="SoilGrids 2.0, SOIL 7, 217-240",
)


def _caracteristique(nom: str, valeur: float, unite: str) -> SolCaracteristique:
    return SolCaracteristique(nom=nom, valeur=valeur, unite=unite, source=_SOURCE)


@pytest.mark.parametrize(
    ("nom", "valeur", "unite", "pourquoi"),
    [
        ("ph", 52.0, "pH", "le défaut SoilGrids exact — facteur dix perdu"),
        ("ph", -1.0, "pH", "hors de l'échelle du pH"),
        ("argile_pct", 500.0, "%", "une part dépasse le tout"),
        ("sable_pct", -3.0, "%", "une part négative"),
        ("carbone", -10.0, "g/kg", "une teneur massique négative"),
    ],
)
def test_une_valeur_hors_de_son_unite_est_refusee(
    nom: str, valeur: float, unite: str, pourquoi: str
) -> None:
    """Le refus nomme la caractéristique, sa valeur et l'intervalle attendu."""
    with pytest.raises(ValidationError, match="hors de"):
        _caracteristique(nom, valeur, unite)


def test_les_valeurs_pedologiques_reelles_restent_acceptees() -> None:
    """Un sol ordinaire passe.

    Sans ce contrôle, borner trop étroitement ferait passer les tests de refus
    tout en rejetant des mesures valides.
    """
    assert _caracteristique("ph", 5.2, "pH").valeur == 5.2
    assert _caracteristique("argile_pct", 28.3, "%").valeur == 28.3
    assert _caracteristique("carbone", 34.0, "g/kg").valeur == 34.0


def test_les_bornes_de_l_echelle_sont_inclusives() -> None:
    """0 et 14 en pH, 0 et 100 en pourcentage sont des valeurs légitimes."""
    assert _caracteristique("ph", 14.0, "pH").valeur == 14.0
    assert _caracteristique("argile_pct", 100.0, "%").valeur == 100.0
    assert _caracteristique("argile_pct", 0.0, "%").valeur == 0.0


def test_une_unite_inconnue_n_est_pas_contrainte() -> None:
    """Mieux vaut ne rien vérifier que vérifier au hasard.

    Une unité absente de la table passe sans contrainte : inventer un
    intervalle pour une unité qu'on ne connaît pas serait exactement
    l'invention que ces bornes existent pour empêcher.
    """
    assert _caracteristique("conductivite", 999.0, "dS/m").valeur == 999.0
