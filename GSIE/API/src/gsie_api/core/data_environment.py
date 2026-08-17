"""Contrat pur de séparation des environnements de données GSIE."""

from __future__ import annotations

from urllib.parse import urlparse

ROLES = frozenset({"development", "test", "benchmark", "staging", "production"})
RESERVED = ("-test", "-benchmark", "-staging", "-production")


def validate_data_environment(
    *,
    environment: str,
    database_role: str,
    namespace: str,
    database_url: str,
    object_bucket: str,
    compose_project: str,
) -> list[str]:
    """Retourne les violations de cloisonnement, sans effet externe."""

    errors: list[str] = []
    if environment not in {"development", "staging", "production"}:
        errors.append("GSIE_ENVIRONMENT invalide")
    if database_role not in ROLES:
        errors.append("GSIE_DATABASE_ROLE invalide")
    if environment in {"staging", "production"} and database_role != environment:
        errors.append("database_role doit correspondre à environment hors développement")
    if database_role != "development" and not namespace.endswith(f"-{database_role}"):
        errors.append("namespace non dédié au rôle")
    if database_role == "development" and namespace.endswith(RESERVED):
        errors.append("namespace réservé utilisé par le développement")
    parsed = urlparse(database_url)
    database_name = parsed.path.lstrip("/")
    if not database_name:
        errors.append("nom de base absent de database_url")
    elif database_role != "development" and not database_name.endswith(f"_{database_role}"):
        errors.append("nom PostgreSQL non dédié au rôle")
    if (
        not object_bucket
        or database_role != "development"
        and not object_bucket.endswith(f"-{database_role}")
    ):
        errors.append("bucket objet non dédié au rôle")
    if (
        not compose_project
        or database_role != "development"
        and not compose_project.endswith(f"-{database_role}")
    ):
        errors.append("projet Compose non dédié au rôle")
    return errors


__all__ = ["validate_data_environment"]
