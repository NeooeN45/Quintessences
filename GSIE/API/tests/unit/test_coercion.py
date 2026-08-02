"""Tests unitaires — coercion des valeurs JSON vers les types SQL.

Couvre les fonctions de conversion de `resources/coercion.py` :
- _coercer_datetime (avec/sans fuseau, instants ambigus)
- _coercer_date (datetime, date, str)
- _coercer_uuid (UUID, str, invalide)
- _coercer_nombre (int, float, Decimal, bool refusé)
- _coercer_geometrie (WKT, EWKT, SRID valide/invalide, malformé)
- coercer_donnees (conversion complète avec colonnes)
- serialiser_valeur (WKBElement, Decimal, autres)
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
import sqlalchemy as sa

from gsie_api.resources.coercion import (
    _coercer_date,
    _coercer_datetime,
    _coercer_geometrie,
    _coercer_nombre,
    _coercer_uuid,
    coercer_donnees,
    serialiser_valeur,
)


class TestCoercerDatetime:
    """Conversion de chaînes ISO vers datetime."""

    def should_parse_iso_string_with_timezone(self) -> None:
        result = _coercer_datetime("2026-01-15T10:00:00Z", avec_fuseau=True)
        assert result.year == 2026
        assert result.tzinfo is not None

    def should_parse_iso_string_without_timezone(self) -> None:
        result = _coercer_datetime("2026-01-15T10:00:00", avec_fuseau=False)
        assert result.tzinfo is None

    def should_accept_datetime_object(self) -> None:
        dt = datetime(2026, 1, 15, 10, 0, 0, tzinfo=UTC)
        result = _coercer_datetime(dt, avec_fuseau=True)
        assert result == dt

    def should_raise_when_naive_datetime_with_timezone_required(self) -> None:
        with pytest.raises(ValueError, match="sans fuseau horaire"):
            _coercer_datetime("2026-01-15T10:00:00", avec_fuseau=True)

    def should_strip_timezone_when_not_required(self) -> None:
        dt = datetime(2026, 1, 15, 10, 0, 0, tzinfo=UTC)
        result = _coercer_datetime(dt, avec_fuseau=False)
        assert result.tzinfo is None

    def should_raise_when_non_string_non_datetime(self) -> None:
        with pytest.raises(ValueError, match="attendu une date-heure"):
            _coercer_datetime(42, avec_fuseau=True)


class TestCoercerDate:
    """Conversion vers date."""

    def should_parse_iso_string(self) -> None:
        result = _coercer_date("2026-01-15")
        assert result == date(2026, 1, 15)

    def should_extract_date_from_datetime(self) -> None:
        dt = datetime(2026, 1, 15, 10, 30, 0)
        result = _coercer_date(dt)
        assert result == date(2026, 1, 15)

    def should_accept_date_object(self) -> None:
        d = date(2026, 1, 15)
        result = _coercer_date(d)
        assert result == d

    def should_raise_when_invalid_type(self) -> None:
        with pytest.raises(ValueError, match="attendu une date"):
            _coercer_date(42)


class TestCoercerUuid:
    """Conversion vers UUID."""

    def should_accept_uuid_object(self) -> None:
        u = uuid4()
        result = _coercer_uuid(u)
        assert result == u

    def should_parse_uuid_string(self) -> None:
        u = uuid4()
        result = _coercer_uuid(str(u))
        assert result == u

    def should_raise_when_invalid_string(self) -> None:
        with pytest.raises(ValueError):
            _coercer_uuid("not-a-uuid")

    def should_raise_when_invalid_type(self) -> None:
        with pytest.raises(ValueError, match="attendu un UUID"):
            _coercer_uuid(42)


class TestCoercerNombre:
    """Conversion vers int, float, Decimal."""

    def should_convert_int(self) -> None:
        result = _coercer_nombre(42, sa.Integer())
        assert result == 42

    def should_convert_float(self) -> None:
        result = _coercer_nombre(3.14, sa.Float())
        assert result == 3.14

    def should_convert_decimal(self) -> None:
        result = _coercer_nombre("3.14", sa.Numeric())
        assert result == Decimal("3.14")

    def should_raise_when_bool_for_number(self) -> None:
        with pytest.raises(ValueError, match="attendu un nombre, reçu un booléen"):
            _coercer_nombre(True, sa.Integer())

    def should_raise_when_invalid_decimal(self) -> None:
        with pytest.raises(ValueError, match="attendu un nombre décimal"):
            _coercer_nombre("not-a-number", sa.Numeric())


class TestCoercerGeometrie:
    """Validation des géométries WKT/EWKT — audit sécurité P2-3."""

    def should_accept_valid_wkt_point(self) -> None:
        result = _coercer_geometrie("POINT(1 2)")
        assert result == "POINT(1 2)"

    def should_accept_valid_wkt_polygon(self) -> None:
        wkt = "POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))"
        result = _coercer_geometrie(wkt)
        assert result == wkt

    def should_accept_ewkt_with_valid_srid_2154(self) -> None:
        result = _coercer_geometrie("SRID=2154;POINT(1 2)")
        assert result == "SRID=2154;POINT(1 2)"

    def should_accept_ewkt_with_valid_srid_4326(self) -> None:
        result = _coercer_geometrie("SRID=4326;POINT(1 2)")
        assert result == "SRID=4326;POINT(1 2)"

    def should_raise_when_srid_not_in_whitelist(self) -> None:
        with pytest.raises(ValueError, match="SRID 9999 non autorisé"):
            _coercer_geometrie("SRID=9999;POINT(1 2)")

    def should_raise_when_srid_zero(self) -> None:
        with pytest.raises(ValueError, match="SRID 0 non autorisé"):
            _coercer_geometrie("SRID=0;POINT(1 2)")

    def should_raise_when_srid_not_numeric(self) -> None:
        with pytest.raises(ValueError, match="SRID illisible"):
            _coercer_geometrie("SRID=abc;POINT(1 2)")

    def should_raise_when_malformed_wkt(self) -> None:
        with pytest.raises(ValueError, match="géométrie illisible"):
            _coercer_geometrie("NOT_A_GEOMETRY")

    def should_raise_when_non_string(self) -> None:
        with pytest.raises(ValueError, match="attendu une géométrie"):
            _coercer_geometrie(42)

    def should_accept_wkt_without_srid_prefix(self) -> None:
        # WKT sans préfixe SRID= — pas de validation SRID, juste WKT
        result = _coercer_geometrie("LINESTRING(0 0, 1 1)")
        assert result == "LINESTRING(0 0, 1 1)"


class TestCoercerDonnees:
    """Conversion complète d'un dictionnaire selon les colonnes d'un modèle."""

    def should_convert_matching_fields(self) -> None:
        # Utilise un modèle SQLAlchemy minimal pour tester
        from sqlalchemy import Column, Integer, String
        from sqlalchemy.orm import DeclarativeBase

        class _Base(DeclarativeBase):
            pass

        class _TestModel(_Base):
            __tablename__ = "test_coercion"
            id = Column(Integer, primary_key=True)
            name = Column(String(100))

        data = {"id": "42", "name": "test"}
        converti, erreurs = coercer_donnees(_TestModel, data)
        assert converti["id"] == 42
        assert converti["name"] == "test"
        assert erreurs == []

    def should_collect_errors_for_invalid_values(self) -> None:
        from sqlalchemy import Column, Integer
        from sqlalchemy.orm import DeclarativeBase

        class _Base(DeclarativeBase):
            pass

        class _TestModel(_Base):
            __tablename__ = "test_coercion_err"
            id = Column(Integer, primary_key=True)
            count = Column(Integer)

        data = {"count": "not-a-number"}
        converti, erreurs = coercer_donnees(_TestModel, data)
        assert len(erreurs) == 1
        assert "count" in erreurs[0]

    def should_pass_through_unknown_fields(self) -> None:
        from sqlalchemy import Column, Integer
        from sqlalchemy.orm import DeclarativeBase

        class _Base(DeclarativeBase):
            pass

        class _TestModel(_Base):
            __tablename__ = "test_coercion_unknown"
            id = Column(Integer, primary_key=True)

        data = {"id": 1, "unknown_field": "value"}
        converti, erreurs = coercer_donnees(_TestModel, data)
        assert converti["unknown_field"] == "value"
        assert erreurs == []

    def should_pass_through_none_values(self) -> None:
        from sqlalchemy import Column, Integer, String
        from sqlalchemy.orm import DeclarativeBase

        class _Base(DeclarativeBase):
            pass

        class _TestModel(_Base):
            __tablename__ = "test_coercion_none"
            id = Column(Integer, primary_key=True)
            name = Column(String(100), nullable=True)

        data = {"id": 1, "name": None}
        converti, erreurs = coercer_donnees(_TestModel, data)
        assert converti["name"] is None
        assert erreurs == []


class TestSerialiserValeur:
    """Sérialisation des valeurs lues en base pour Pydantic."""

    def should_convert_decimal_to_float(self) -> None:
        result = serialiser_valeur(Decimal("3.14"))
        assert result == 3.14
        assert isinstance(result, float)

    def should_pass_through_strings(self) -> None:
        result = serialiser_valeur("hello")
        assert result == "hello"

    def should_pass_through_integers(self) -> None:
        result = serialiser_valeur(42)
        assert result == 42

    def should_pass_through_none(self) -> None:
        result = serialiser_valeur(None)
        assert result is None
