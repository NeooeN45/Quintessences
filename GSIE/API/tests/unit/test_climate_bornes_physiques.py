"""Une valeur qui n'est pas une mesure n'entre pas dans un diagnostic.

`engine.py` convertit les températures SYNOP de Kelvin en Celsius par
soustraction de 273,15. Rien ne garantissait le sens de l'opération : une
valeur déjà exprimée en Celsius, ou une conversion appliquée deux fois,
produisait **-253 °C** — sous le zéro absolu — et le schéma l'acceptait sans
objection. Vérifié avant correction, de même pour une humidité de 250 %, un
azimut de 999° et une vitesse de vent négative.

Ces bornes sont **définitionnelles, jamais empiriques**, et c'est ce qui les
rend admissibles au regard d'`ADR-009`. « Au-delà de 50 °C, suspect » exigerait
une source climatologique et resterait un jugement. « Sous le zéro absolu,
impossible » n'en exige aucune : c'est la définition de l'échelle Celsius
adossée au kelvin, BIPM (2019) §2.3.1, déjà citée dans `engine.py`.

Ces contrôles n'attrapent donc pas une valeur douteuse — ils attrapent une
valeur qui n'est pas une mesure.

**Limite assumée, établie en écrivant ces tests.** La borne du zéro absolu
n'attrape la double conversion que si la valeur d'origine était négative :
-5 °C mal converti donne -278,15 °C et tombe, mais 20 °C mal converti donne
-253,15 °C — au-dessus du zéro absolu — et **passe**.

Attraper ce cas-là supposerait une borne climatologique, par exemple le record
mondial de -89,2 °C relevé à Vostok. Ce serait une borne **empirique**,
exigeant sa source et relevant d'un arbitrage, non d'une définition. Elle n'est
donc pas posée ici. La limite est écrite plutôt que tue : croire ces bornes
suffisantes contre les erreurs d'unité serait s'en remettre à une protection
qu'elles n'offrent pas.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from gsie_api.engines.climate.schemas import ObservationClimatique
from gsie_api.engines.evidence.schemas import SourceReference, SourceType

_SOURCE = SourceReference(
    type_source=SourceType.referentiel_officiel,
    auteur="Météo-France",
    reference="Données d'observation SYNOP, licence ouverte 2.0",
)


def _observation(**mesures: float) -> ObservationClimatique:
    """Observation SYNOP valide, dont on ne remplace que les mesures visées."""
    return ObservationClimatique(
        requete_id=uuid4(),
        station_id="07510",
        nom_station="BORDEAUX-MERIGNAC",
        latitude=44.83,
        longitude=-0.69,
        date_observation=datetime.now(UTC),
        source=_SOURCE,
        **mesures,
    )


@pytest.mark.parametrize(
    ("champ", "valeur", "pourquoi"),
    [
        (
            "temperature_c",
            -5.0 - 273.15,
            "conversion Kelvin appliquée à une valeur hivernale déjà en Celsius",
        ),
        ("temperature_c", -300.0, "sous le zéro absolu"),
        ("humidite_pct", 250.0, "pourcentage de saturation au-delà de la saturation"),
        ("humidite_pct", -5.0, "pourcentage négatif"),
        ("vent_direction_deg", 999.0, "azimut hors du cercle"),
        ("vent_vitesse_ms", -5.0, "une vitesse est une norme"),
        ("precipitations_1h_mm", -1.0, "une hauteur accumulée ne décroît pas"),
        ("pression_hpa", 0.0, "une pression absolue n'est jamais nulle"),
    ],
)
def test_une_valeur_physiquement_impossible_est_refusee(
    champ: str, valeur: float, pourquoi: str
) -> None:
    """Chaque mesure hors de sa définition est refusée à la construction."""
    with pytest.raises(ValidationError):
        _observation(**{champ: valeur})


def test_les_valeurs_reelles_restent_acceptees() -> None:
    """Une observation ordinaire passe, bornes comprises.

    Sans ce contrôle, borner trop étroitement ferait passer les tests
    précédents tout en refusant des mesures valides — et une station en gelée
    ou un vent plein nord se verraient rejetés.
    """
    obs = _observation(
        temperature_c=-25.0,
        humidite_pct=100.0,
        vent_direction_deg=0.0,
        vent_vitesse_ms=0.0,
        precipitations_1h_mm=0.0,
        pression_hpa=1013.25,
    )

    assert obs.temperature_c == -25.0
    assert obs.humidite_pct == 100.0
    assert obs.vent_direction_deg == 0.0


def test_les_bornes_du_cercle_et_de_la_saturation_sont_inclusives() -> None:
    """360° et 100 % sont des valeurs légitimes, pas des dépassements."""
    obs = _observation(vent_direction_deg=360.0, humidite_pct=100.0)

    assert obs.vent_direction_deg == 360.0
    assert obs.humidite_pct == 100.0
