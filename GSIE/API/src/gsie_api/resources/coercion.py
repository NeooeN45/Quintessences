"""Conversion des valeurs JSON vers les types Python attendus par les colonnes.

L'API générique `/resources` accepte `data` en `dict[str, Any]` : aucune
coercition Pydantic ne s'applique, et la valeur arrivait telle quelle dans la
colonne. Une chaîne ISO envoyée vers un `timestamptz` faisait donc échouer le
pilote asyncpg *après* la porte de validation, et le client recevait un 500
opaque au lieu d'un 422 explicable.

Ce module tient les deux bouts :

* :func:`coercer_donnees` convertit selon le type SQL réel de chaque colonne et
  transforme tout échec en message de validation — jamais en erreur pilote ;
* :func:`serialiser_valeur` fait le chemin inverse à la lecture, pour les types
  que Pydantic ne sait pas sérialiser (géométries PostGIS).
"""

from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

import sqlalchemy as sa

__all__ = ["coercer_donnees", "serialiser_valeur"]

# Préfixe EWKT (`SRID=2154;POINT(...)`) — shapely ne lit que le WKT nu.
_SEPARATEUR_EWKT = ";"
_PREFIXE_SRID = "SRID="


def _coercer_datetime(valeur: Any, avec_fuseau: bool) -> datetime:
    """Convertit une chaîne ISO en datetime, en refusant les instants ambigus."""
    if isinstance(valeur, datetime):
        instant = valeur
    elif isinstance(valeur, str):
        # `datetime.fromisoformat` de Python 3.12 accepte le suffixe « Z ».
        instant = datetime.fromisoformat(valeur)
    else:
        raise ValueError(f"attendu une date-heure ISO 8601, reçu {type(valeur).__name__}")

    if avec_fuseau and instant.tzinfo is None:
        # Un instant naïf stocké en `timestamptz` serait silencieusement
        # réinterprété dans le fuseau du serveur : on impose l'explicite.
        raise ValueError(
            "date-heure sans fuseau horaire : préciser le décalage (ex. « 2026-01-15T10:00:00Z »)"
        )
    if not avec_fuseau and instant.tzinfo is not None:
        instant = instant.astimezone(UTC).replace(tzinfo=None)
    return instant


def _coercer_date(valeur: Any) -> date:
    if isinstance(valeur, datetime):
        return valeur.date()
    if isinstance(valeur, date):
        return valeur
    if isinstance(valeur, str):
        return date.fromisoformat(valeur)
    raise ValueError(f"attendu une date ISO 8601, reçu {type(valeur).__name__}")


def _coercer_uuid(valeur: Any) -> UUID:
    if isinstance(valeur, UUID):
        return valeur
    if isinstance(valeur, str):
        return UUID(valeur)
    raise ValueError(f"attendu un UUID, reçu {type(valeur).__name__}")


def _coercer_nombre(valeur: Any, colonne_type: Any) -> Any:
    if isinstance(valeur, bool):
        # `bool` est un `int` en Python : refuser explicitement plutôt que
        # d'écrire 0/1 dans une colonne numérique métier.
        raise ValueError("attendu un nombre, reçu un booléen")
    if isinstance(colonne_type, sa.Numeric) and not isinstance(colonne_type, sa.Float):
        try:
            return Decimal(str(valeur))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"attendu un nombre décimal, reçu « {valeur} »") from exc
    if isinstance(colonne_type, sa.Float):
        return float(valeur)
    return int(valeur)


def _coercer_geometrie(valeur: Any) -> str:
    """Vérifie qu'une géométrie est lisible avant de la confier à PostGIS.

    Sans ce contrôle, un WKT malformé remonte en `InternalServerError` depuis
    `ST_GeomFromEWKT`, donc en 500 côté client.
    """
    if not isinstance(valeur, str):
        raise ValueError(f"attendu une géométrie WKT ou EWKT, reçu {type(valeur).__name__}")

    corps = valeur
    if valeur.upper().startswith(_PREFIXE_SRID) and _SEPARATEUR_EWKT in valeur:
        corps = valeur.split(_SEPARATEUR_EWKT, 1)[1]

    from shapely import wkt  # import local : shapely est lourd à charger

    try:
        wkt.loads(corps)
    except Exception as exc:
        raise ValueError(f"géométrie illisible : {exc}") from exc
    return valeur


def _coercer_valeur(valeur: Any, colonne: Any) -> Any:
    """Convertit une valeur selon le type SQL de sa colonne."""
    type_sql = colonne.type

    # Les géométries se reconnaissent au nom : GeoAlchemy2 n'hérite pas des
    # types SQLAlchemy natifs.
    if type(type_sql).__name__ in {"Geometry", "Geography"}:
        return _coercer_geometrie(valeur)
    if isinstance(type_sql, sa.DateTime):
        return _coercer_datetime(valeur, avec_fuseau=bool(getattr(type_sql, "timezone", False)))
    if isinstance(type_sql, sa.Date):
        return _coercer_date(valeur)
    if isinstance(type_sql, sa.Uuid):
        return _coercer_uuid(valeur)
    if isinstance(type_sql, sa.Boolean):
        if isinstance(valeur, bool):
            return valeur
        raise ValueError(f"attendu un booléen, reçu {type(valeur).__name__}")
    if isinstance(type_sql, sa.Numeric | sa.Integer):
        return _coercer_nombre(valeur, type_sql)
    return valeur


def coercer_donnees(model_cls: type[Any], data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Convertit `data` vers les types des colonnes de `model_cls`.

    Returns:
        Le dictionnaire converti et la liste des erreurs de conversion. Une
        valeur en erreur est laissée de côté : c'est l'appelant qui décide
        d'interrompre, en remontant les erreurs au format de la porte de
        validation (donc en 422).
    """
    colonnes = {colonne.name: colonne for colonne in model_cls.__table__.columns}
    converti: dict[str, Any] = {}
    erreurs: list[str] = []

    for champ, valeur in data.items():
        colonne = colonnes.get(champ)
        if colonne is None or valeur is None:
            converti[champ] = valeur
            continue
        try:
            converti[champ] = _coercer_valeur(valeur, colonne)
        except (ValueError, TypeError, OverflowError) as exc:
            erreurs.append(f"Valeur invalide pour {champ} : {exc}")

    return converti, erreurs


def serialiser_valeur(valeur: Any) -> Any:
    """Rend une valeur lue en base sérialisable par Pydantic.

    Une géométrie relue est un `WKBElement`, que Pydantic ne sait pas rendre :
    la ressource était écrite puis devenait illisible (500 permanent sur la
    lecture unitaire). On la restitue en WKT, forme que l'API accepte aussi en
    écriture — l'aller-retour reste donc cohérent.
    """
    if type(valeur).__name__ in {"WKBElement", "WKTElement"}:
        from geoalchemy2.shape import to_shape

        return to_shape(valeur).wkt
    if isinstance(valeur, Decimal):
        return float(valeur)
    return valeur
