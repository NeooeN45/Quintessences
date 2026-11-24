"""Régression GHSA-f56c-v883-vx8r : pas de balayage par paramètre inconnu.

Chaque ``getlist`` Starlette parcourt les entrées reçues. Compter ces
balayages rend la preuve déterministe, sans seuil de temps fragile ni charge
hostile : 256 petits paramètres au maximum et aucun réseau externe.
"""

from typing import Annotated, Any

import pytest
from fastapi import FastAPI, File, Form, Header, Query, UploadFile
from fastapi.testclient import TestClient
from starlette.datastructures import FormData, Headers, QueryParams


def _application() -> FastAPI:
    app = FastAPI()

    @app.get("/requete")
    def requete(cle: Annotated[list[str], Query()]) -> dict[str, list[str]]:
        return {"cle": cle}

    @app.get("/entetes")
    def entetes(x_cle: Annotated[list[str], Header()]) -> dict[str, list[str]]:
        return {"cle": x_cle}

    @app.post("/formulaire")
    async def formulaire(
        cle: Annotated[list[str], Form()], fichier: Annotated[UploadFile, File()]
    ) -> dict[str, Any]:
        return {"cle": cle, "fichier": (await fichier.read()).decode("ascii")}

    return app


@pytest.mark.parametrize("nombre", [64, 256])
@pytest.mark.parametrize("canal", ["requete", "entetes", "formulaire"])
def should_borner_les_balayages_when_parametres_inconnus_nombreux(
    monkeypatch: pytest.MonkeyPatch, nombre: int, canal: str
) -> None:
    """Conserve aussi les valeurs répétées et le fichier pendant l'extraction."""
    collection = {"requete": QueryParams, "entetes": Headers, "formulaire": FormData}[canal]
    getlist = collection.getlist
    balayages = 0

    def compter(self: Any, cle: str) -> list[Any]:
        nonlocal balayages
        balayages += 1
        return getlist(self, cle)

    monkeypatch.setattr(collection, "getlist", compter)
    inconnus = [(f"inconnu-{i}", "x") for i in range(nombre)]
    with TestClient(_application()) as client:
        if canal == "requete":
            response = client.get("/requete", params=[("cle", "a"), ("cle", "b"), *inconnus])
        elif canal == "entetes":
            response = client.get("/entetes", headers=[("x-cle", "a"), ("x-cle", "b"), *inconnus])
        else:
            champs = [
                (nom, (None, valeur)) for nom, valeur in [("cle", "a"), ("cle", "b"), *inconnus]
            ]
            response = client.post(
                "/formulaire", files=[*champs, ("fichier", ("test.txt", b"gsie"))]
            )

    assert response.status_code == 200
    attendu: dict[str, Any] = {"cle": ["a", "b"]}
    if canal == "formulaire":
        attendu["fichier"] = "gsie"
    assert response.json() == attendu
    assert balayages <= 8, f"{canal} : {balayages} balayages pour {nombre} paramètres inconnus"
