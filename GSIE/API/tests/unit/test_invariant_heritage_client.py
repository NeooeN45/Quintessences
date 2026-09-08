"""Invariant — tout client d'API externe doit hériter de ResilientHttpClient.

GSIE-PROMPT-0024 raccorde les 10 clients d'API externes sur la base
class `ResilientHttpClient` (ou `ResilientCsvClient`). Cet invariant
vérifie que le raccordement est en place et reste en place — sans lui,
un client pourrait être ajouté ou modifié sans la capture automatique
des 5 modes de panne, et rien ne le signalerait.

Le test énumère tous les clients connus et vérifie `issubclass(client,
ResilientHttpClient)`. Un client non raccordable doit être déclaré
explicitement dans `NON_RACCORDABLES` avec son motif.

Pour prouver que le test n'est pas un passe-partout, on vérifie aussi
qu'il échoue si on lui donne une classe qui n'hérite pas de la base.
"""

from __future__ import annotations

from gsie_api.data.soilgrids_wcs_client import SoilGridsWcsClient
from gsie_api.engines.botanical.gbif_client import GBIFClient
from gsie_api.engines.botanical.taxref_client import TaxrefClient
from gsie_api.engines.climate.arome_client import AromeClient
from gsie_api.engines.climate.dpclim_client import DPClimClient
from gsie_api.engines.climate.meteofrance_client import MeteoFranceClient
from gsie_api.engines.climate.paquet_observation_client import PaquetObservationClient
from gsie_api.engines.climate.synop_client import SynopClient
from gsie_api.engines.climate.vigilance_client import VigilanceClient
from gsie_api.engines.gis.ign_client import IGNClient
from gsie_api.shared.http_client import ResilientCsvClient, ResilientHttpClient

# Clients d'API externes — tout nouveau client doit être ajouté ici.
CLIENTS_API_EXTERNES: dict[str, type] = {
    "GBIFClient": GBIFClient,
    "TaxrefClient": TaxrefClient,
    "SoilGridsWcsClient": SoilGridsWcsClient,
    "IGNClient": IGNClient,
    "VigilanceClient": VigilanceClient,
    "MeteoFranceClient": MeteoFranceClient,
    "SynopClient": SynopClient,
    "PaquetObservationClient": PaquetObservationClient,
    "DPClimClient": DPClimClient,
    "AromeClient": AromeClient,
}

# Clients déclarés non raccordables avec motif explicite.
# Vide en Phase 4 — les 10 clients sont raccordés.
NON_RACCORDABLES: dict[str, str] = {}


def test_tout_client_api_externe_herite_de_resilient_http_client() -> None:
    """Chaque client d'API externe doit hériter de ResilientHttpClient.

    Sans cet héritage, la capture des 5 modes de panne (réseau, HTTP
    4xx/5xx, JSON malformé, champ absent, quota/auth) n'est pas
    automatique — il faut la réimplémenter manuellement, et l'audit de
    fiabilité a montré que ça finit toujours par être oublié.
    """
    manquants: list[str] = []
    for nom, classe in CLIENTS_API_EXTERNES.items():
        if nom in NON_RACCORDABLES:
            continue
        if not issubclass(classe, ResilientHttpClient):
            manquants.append(nom)

    assert manquants == [], (
        f"Clients non raccordés sur ResilientHttpClient : {sorted(manquants)}. "
        "Soit les raccorder sur ResilientHttpClient/ResilientCsvClient, "
        "soit les déclarer dans NON_RACCORDABLES avec un motif."
    )


def test_aucun_client_non_raccordable_sans_motif() -> None:
    """Chaque client déclaré non raccordable doit avoir un motif explicite."""
    sans_motif = [nom for nom, motif in NON_RACCORDABLES.items() if not motif.strip()]
    assert sans_motif == [], f"Clients non raccordables sans motif : {sorted(sans_motif)}"


def test_le_test_echoue_si_un_client_ne_herite_pas() -> None:
    """Garantie que le test d'invariant n'est pas un passe-partout.

    Si on remplace un client par une classe qui n'hérite pas de
    ResilientHttpClient, le test doit le détecter. On le prouve en
    injectant un faux client non raccordé.
    """

    class FauxClientNonRaccorde:
        """Client qui n'hérite pas de ResilientHttpClient — doit être détecté."""

    faux_registre: dict[str, type] = {**CLIENTS_API_EXTERNES, "FauxClient": FauxClientNonRaccorde}
    manquants = [
        nom
        for nom, classe in faux_registre.items()
        if nom not in NON_RACCORDABLES and not issubclass(classe, ResilientHttpClient)
    ]
    assert "FauxClient" in manquants, (
        "Le test d'invariant n'a pas détecté FauxClientNonRaccorde — " "il ne sert à rien."
    )


def test_clients_csv_herite_de_resilient_csv_client() -> None:
    """Les clients qui retournent du CSV doivent hériter de ResilientCsvClient."""
    clients_csv: dict[str, type] = {
        "MeteoFranceClient": MeteoFranceClient,
        "PaquetObservationClient": PaquetObservationClient,
    }
    manquants: list[str] = []
    for nom, classe in clients_csv.items():
        if not issubclass(classe, ResilientCsvClient):
            manquants.append(nom)

    assert (
        manquants == []
    ), f"Clients CSV non raccordés sur ResilientCsvClient : {sorted(manquants)}"
