"""Tests unitaires — passeport de décision (RFC-0016 §3.4, Phase B point 6).

Vérifie que chaque catégorie du passeport de décision impose sa propre
justification non négociable : un élément classé « modélisé » sans
référence au modèle, ou « incertain » sans motif, doit être refusé —
jamais une valeur affichée sans la preuve qui la classe.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from gsie_api.shared.schemas import DecisionPassport, DecisionPassportItem


def test_observe_requires_protocol_or_method() -> None:
    item = DecisionPassportItem(
        label="Surface terrière mesurée",
        value="28 m²/ha",
        category="observe",
        protocol_or_method="Relevé IFN, placette circulaire 700 m²",
    )
    assert item.category == "observe"


def test_observe_without_protocol_raises() -> None:
    with pytest.raises(ValidationError, match="protocol_or_method"):
        DecisionPassportItem(
            label="Surface terrière mesurée",
            value="28 m²/ha",
            category="observe",
        )


def test_calcule_requires_method() -> None:
    item = DecisionPassportItem(
        label="Surface terrière calculée",
        value="27.8 m²/ha",
        category="calcule",
        method="G = (π/4) × D² × N",
    )
    assert item.method is not None


def test_calcule_without_method_raises() -> None:
    with pytest.raises(ValidationError, match="method"):
        DecisionPassportItem(
            label="Surface terrière calculée",
            value="27.8 m²/ha",
            category="calcule",
        )


def test_modelise_requires_model_reference() -> None:
    item = DecisionPassportItem(
        label="Classe de fertilité modélisée",
        value="Classe 1",
        category="modelise",
        model_reference=uuid4(),
    )
    assert item.model_reference is not None


def test_modelise_without_model_reference_raises() -> None:
    with pytest.raises(ValidationError, match="model_reference"):
        DecisionPassportItem(
            label="Classe de fertilité modélisée",
            value="Classe 1",
            category="modelise",
        )


def test_documente_recommande_requires_source_page_or_table() -> None:
    item = DecisionPassportItem(
        label="Éclaircie recommandée",
        value="Prélever 25 % de la surface terrière",
        category="documente_recommande",
        source_page_or_table="Guide sylvicole régional, p. 58",
    )
    assert item.source_page_or_table is not None


def test_documente_recommande_without_source_raises() -> None:
    with pytest.raises(ValidationError, match="source_page_or_table"):
        DecisionPassportItem(
            label="Éclaircie recommandée",
            value="Prélever 25 % de la surface terrière",
            category="documente_recommande",
        )


def test_incertain_requires_uncertainty_reason() -> None:
    item = DecisionPassportItem(
        label="Agent causal du dépérissement",
        value="Suspecté, non confirmé",
        category="incertain",
        uncertainty_reason="Deux protocoles en désaccord, pas d'analyse de laboratoire",
    )
    assert item.uncertainty_reason is not None


def test_incertain_without_reason_raises() -> None:
    with pytest.raises(ValidationError, match="uncertainty_reason"):
        DecisionPassportItem(
            label="Agent causal du dépérissement",
            value="Suspecté, non confirmé",
            category="incertain",
        )


def test_decision_passport_requires_at_least_one_item() -> None:
    with pytest.raises(ValidationError):
        DecisionPassport(
            subject_id=uuid4(),
            items=[],
            generated_at=datetime(2026, 7, 19, tzinfo=UTC),
        )


def test_decision_passport_accepts_mixed_categories() -> None:
    passport = DecisionPassport(
        subject_id=uuid4(),
        items=[
            DecisionPassportItem(
                label="Surface terrière mesurée",
                value="28 m²/ha",
                category="observe",
                protocol_or_method="Relevé IFN, placette circulaire 700 m²",
            ),
            DecisionPassportItem(
                label="Classe de fertilité modélisée",
                value="Classe 1",
                category="modelise",
                model_reference=uuid4(),
            ),
        ],
        generated_at=datetime(2026, 7, 19, tzinfo=UTC),
    )
    assert len(passport.items) == 2
