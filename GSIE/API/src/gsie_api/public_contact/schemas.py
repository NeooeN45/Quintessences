"""Contrats de l'endpoint de contact public, sans persistance du message."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ContactCategory(StrEnum):
    """Catégories affichées par le formulaire public."""

    partenariat = "partenariat"
    presse = "presse"
    securite = "securite"
    support = "support"
    autre = "autre"


class PublicContactRequest(BaseModel):
    """Message entrant borné et validé avant tout traitement externe."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email: EmailStr
    category: ContactCategory
    message: str = Field(min_length=10, max_length=5000)
    turnstile_token: str = Field(default="", max_length=2048)
    website: str = Field(default="", max_length=100)


class PublicContactResponse(BaseModel):
    """Accusé de réception générique, sans exposer le destinataire interne."""

    model_config = ConfigDict(extra="forbid")

    accepted: bool = True
    message: str = "Votre message a été transmis."

