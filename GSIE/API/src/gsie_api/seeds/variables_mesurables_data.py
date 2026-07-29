"""Vocabulaire contrôlé des grandeurs mesurables — RFC-0028 §4.4, DEC-000038.

Sans référentiel commun, « RUM », « réserve utile » et `reserve_utile_mm`
désignent la même grandeur sans qu'aucun rapprochement soit possible : une
règle dérivée est retournée, puis échoue en silence parce que le fait de la
station ne porte pas le même nom. Un échec silencieux vaut ici une absence de
connaissance que personne ne voit passer.

Ce module ne crée aucune grandeur : il **enregistre celles qu'une source fait
autorité pour définir** (`GSIE-CON-005`). Une variable sans définition sourcée
n'entre pas au vocabulaire — elle resterait citable sans être vérifiable.

Distinction structurante relevée à l'inventaire : les variables employées dans
le dépôt se répartissent en deux familles.

* **quantitatives** — `reserve_utile_mm`, `ph_optimal`, `profondeur_cm` :
  comparables, donc dérivables en condition de règle ;
* **qualitatives** — `tolerance_secheresse`, `exigence_lumiere` : Rameau 2008
  les présente en préférences et non en seuils chiffrés. Aucune condition
  numérique ne peut en sortir (`ADR-009`).

Seules les premières figurent ici. Le vocabulaire des secondes relève d'une
autre décision, car comparer « moyenne » à « forte » suppose un ordre que la
source ne déclare pas toujours.
"""

from __future__ import annotations

from dataclasses import dataclass

from gsie_api.engines.evidence.schemas import SourceReference, SourceType

__all__ = [
    "NAMESPACE_VARIABLES",
    "NOM_VOCABULAIRE",
    "VariableMesurable",
    "source_reserve_utile_inrae",
    "variables_mesurables",
]

NOM_VOCABULAIRE = "Grandeurs mesurables GSIE"
NAMESPACE_VARIABLES = "gsie:variable"


def source_reserve_utile_inrae() -> SourceReference:
    """Réservoir utile des sols de la France métropolitaine, INRAE (2021).

    Référentiel institutionnel, licence Etalab 2.0, identifiant pérenne DOI.
    Le jeu publie ses incertitudes (écart-type et variance) — rare, et
    déterminant pour un système dont le produit est la connaissance.

    Grain natif : 90 m, soit 8100 m² (`NOMENCLATURE_SOURCES.md` §4).
    """
    return SourceReference(
        type_source=SourceType.referentiel_officiel,
        auteur="Román Dobarco M., Bourennane H., Arrouays D., Saby N., Cousin I., Martin M.",
        date_publication="2021",
        reference=(
            "Réservoir utile des sols de la France métropolitaine, version 2.0, "
            "INRAE, doi:10.15454/9IRARJ"
        ),
        version_source="2.0",
    )


@dataclass(frozen=True)
class VariableMesurable:
    """Une grandeur quantitative, son unité et la source qui la définit."""

    code: str
    label: str
    unite: str
    definition: str
    source: SourceReference


def variables_mesurables() -> list[VariableMesurable]:
    """Grandeurs dont une source fait autorité pour la définition.

    Volontairement restreint au périmètre pilote acté par `DEC-000038` —
    chêne sessile, réserve utile maximale, un territoire. Élargir suppose
    d'apporter la source qui définit chaque grandeur ajoutée, jamais de
    compléter par analogie.
    """
    return [
        VariableMesurable(
            code="reserve_utile_mm",
            label="Réserve utile du sol",
            unite="mm",
            definition=(
                "Quantité maximale d'eau qu'un sol peut retenir et restituer aux "
                "plantes, intégrée sur la profondeur de sol estimée (maximum "
                "2 m). La source tronque chaque horizon à la profondeur de sol "
                "réelle : sur un sol superficiel, les tranches profondes ne "
                "contribuent pas. Reste distincte de la réserve effectivement "
                "accessible aux racines, qui dépend de l'enracinement de "
                "l'essence et constitue une valeur dérivée."
            ),
            source=source_reserve_utile_inrae(),
        ),
    ]


def codes_variables_mesurables() -> frozenset[str]:
    """Codes admis dans une condition de règle dérivée.

    C'est ce jeu que `deriver_regle` reçoit en `variables_connues` : une
    variable absente est refusée plutôt que rapprochée par ressemblance.
    """
    return frozenset(variable.code for variable in variables_mesurables())
