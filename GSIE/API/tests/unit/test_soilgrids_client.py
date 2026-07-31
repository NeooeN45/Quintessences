"""Tests unitaires — SoilGridsClient (résilience aux pannes amont).

Couvre les 5 modes de panne pour le client SoilGrids (ISRIC).
Aucune authentification requise — le mode #5 (quota/auth) est
déclaré N/A pour ce client.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from httpx import Response

from gsie_api.engines.pedology.soilgrids_client import (
    _SOILGRIDS_URL,
    SoilGridsClient,
    SoilGridsClientError,
)


@respx.mock
async def test_should_raise_soilgrids_client_error_when_connect_error() -> None:
    """Mode #1 — une panne réseau (ConnectError) doit lever SoilGridsClientError."""
    respx.get(_SOILGRIDS_URL).mock(side_effect=httpx.ConnectError("connexion refusée"))
    client = SoilGridsClient()
    with pytest.raises(SoilGridsClientError, match="Échec de l'appel SoilGrids"):
        await client.get_properties(44.8, -0.6, ["phh2o"])


@respx.mock
async def test_should_raise_soilgrids_client_error_when_http_4xx_then_5xx() -> None:
    """Mode #2 — un statut HTTP 4xx puis 5xx doit lever SoilGridsClientError."""
    client = SoilGridsClient()
    respx.get(_SOILGRIDS_URL).mock(return_value=Response(404))
    with pytest.raises(SoilGridsClientError):
        await client.get_properties(44.8, -0.6, ["phh2o"])

    respx.get(_SOILGRIDS_URL).mock(return_value=Response(500))
    with pytest.raises(SoilGridsClientError):
        await client.get_properties(44.8, -0.6, ["phh2o"])


@respx.mock
async def test_should_raise_soilgrids_client_error_when_json_invalid() -> None:
    """Mode #3 — un corps JSON malformé doit lever SoilGridsClientError."""
    respx.get(_SOILGRIDS_URL).mock(return_value=Response(200, content=b"<<< pas du JSON >>>"))
    client = SoilGridsClient()
    with pytest.raises(SoilGridsClientError):
        await client.get_properties(44.8, -0.6, ["phh2o"])


@respx.mock
async def test_should_return_empty_dict_when_layers_absent_in_valid_json() -> None:
    """Mode #4 — une réponse JSON valide mais sans 'layers' doit retourner un dict vide.

    Le cas le plus dangereux : une réponse bien formée sans les données
    attendues. La garde utilise data.get("properties", {}).get("layers", [])
    qui retourne [] silencieusement — le résultat doit être un dict vide,
    jamais une valeur inventée.
    """
    respx.get(_SOILGRIDS_URL).mock(
        return_value=Response(200, json={"properties": {}, "status": "ok"})
    )
    client = SoilGridsClient()
    result = await client.get_properties(44.8, -0.6, ["phh2o"])
    assert result == {}


async def test_mode5_quota_auth_not_applicable_for_soilgrids() -> None:
    """Mode #5 — N/A : l'API SoilGrids ne requiert aucune authentification."""
    pass


# --- L'echelle de la valeur ne se suppose pas ---


def _reponse_ph(mean: int, unit_measure: dict | None) -> dict:
    """Réponse SoilGrids d'une seule couche pH, avec ou sans facteur d'échelle."""
    couche: dict = {"name": "phh2o", "depths": [{"values": {"mean": mean}}]}
    if unit_measure is not None:
        couche["unit_measure"] = unit_measure
    return {"properties": {"layers": [couche]}}


@respx.mock
async def test_should_refuse_a_layer_without_scale_factor() -> None:
    """Une couche sans `d_factor` est refusée, jamais divisée par un supposé 1.

    Défaut reproduit avant correction : `layer.get("unit_measure", {}).get(
    "d_factor", 1)` retombait sur l'identité. Une couche `phh2o` de moyenne 52 —
    soit un pH de 5,2 mis à l'échelle par dix, comme SoilGrids le fait — sortait
    à **pH 52**, hors de l'échelle physique 0–14.

    La conséquence est silencieuse et grave : la règle `pedologie_pH < 5.5`
    évalue alors `52 < 5.5`, donc Faux, et un sol acide se diagnostique basique.
    Aucune erreur n'est levée, aucune trace ne signale l'inversion.

    Un facteur absent ne vaut pas un : il signifie que l'échelle est inconnue.
    """
    respx.get(_SOILGRIDS_URL).mock(return_value=Response(200, json=_reponse_ph(52, None)))

    with pytest.raises(SoilGridsClientError, match="échelle de la valeur est inconnue"):
        await SoilGridsClient().get_properties(44.8, -0.6, ["phh2o"])


@respx.mock
async def test_should_accept_an_explicit_scale_factor_of_one() -> None:
    """`d_factor` valant explicitement 1 reste légitime.

    Certaines propriétés SoilGrids sont déjà dans l'unité cible. C'est
    l'**omission** qui est refusée, pas la valeur — sans ce contrôle, la
    correction refuserait des réponses parfaitement valides.
    """
    respx.get(_SOILGRIDS_URL).mock(
        return_value=Response(200, json=_reponse_ph(7, {"d_factor": 1, "target_units": "-"}))
    )

    resultat = await SoilGridsClient().get_properties(44.8, -0.6, ["phh2o"])

    assert resultat["phh2o"] == 7.0


@respx.mock
async def test_should_apply_the_declared_scale_factor() -> None:
    """Le facteur déclaré est appliqué : 52 divisé par dix fait bien pH 5,2.

    Sans ce contrôle, refuser toute couche ferait passer le premier test — et
    le client ne rendrait plus jamais de valeur.
    """
    respx.get(_SOILGRIDS_URL).mock(
        return_value=Response(200, json=_reponse_ph(52, {"d_factor": 10, "mapped_units": "pH*10"}))
    )

    resultat = await SoilGridsClient().get_properties(44.8, -0.6, ["phh2o"])

    assert resultat["phh2o"] == pytest.approx(5.2)
    assert 0 <= resultat["phh2o"] <= 14, "le pH doit rester dans l'échelle physique"


@respx.mock
async def test_should_refuse_a_null_scale_factor() -> None:
    """Un `d_factor` nul est refusé plutôt que de lever une division par zéro."""
    respx.get(_SOILGRIDS_URL).mock(
        return_value=Response(200, json=_reponse_ph(52, {"d_factor": 0}))
    )

    with pytest.raises(SoilGridsClientError, match="`d_factor` nul"):
        await SoilGridsClient().get_properties(44.8, -0.6, ["phh2o"])
