"""Tests unitaires pour l'extension du contexte RLS avec workspace_id.

Valide que ``set_rls_context`` accepte un ``workspace_id`` optionnel
et que ``get_db_rls`` l'extrait depuis le JWT.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from gsie_api.infrastructure.database import set_rls_context


def _extract_params(call_obj: object) -> dict[str, str]:
    """Extrait le dict de paramètres d'un appel mock à session.execute."""
    # call_obj est un call : (TextClause, {"uid": "..."})
    args = call_obj.args  # type: ignore[attr-defined]
    if len(args) >= 2 and isinstance(args[1], dict):
        return args[1]
    return {}


@pytest.mark.asyncio
async def test_set_rls_context_without_workspace_id() -> None:
    """set_rls_context pose user_id et roles, pas workspace_id."""
    session = MagicMock()
    session.execute = AsyncMock()

    await set_rls_context(session, "user-123", "admin,researcher")

    assert session.execute.call_count == 2
    params_0 = _extract_params(session.execute.call_args_list[0])
    params_1 = _extract_params(session.execute.call_args_list[1])
    assert params_0.get("uid") == "user-123"
    assert params_1.get("roles") == "admin,researcher"


@pytest.mark.asyncio
async def test_set_rls_context_with_workspace_id() -> None:
    """set_rls_context pose user_id, roles et workspace_id quand fourni."""
    session = MagicMock()
    session.execute = AsyncMock()

    await set_rls_context(session, "user-123", "admin", workspace_id="ws-456")

    assert session.execute.call_count == 3
    params_0 = _extract_params(session.execute.call_args_list[0])
    params_1 = _extract_params(session.execute.call_args_list[1])
    params_2 = _extract_params(session.execute.call_args_list[2])
    assert params_0.get("uid") == "user-123"
    assert params_1.get("roles") == "admin"
    assert params_2.get("wid") == "ws-456"


@pytest.mark.asyncio
async def test_set_rls_context_with_none_workspace_id() -> None:
    """set_rls_context ignore workspace_id=None (pas de 3e appel)."""
    session = MagicMock()
    session.execute = AsyncMock()

    await set_rls_context(session, "user-123", "admin", workspace_id=None)

    assert session.execute.call_count == 2


def test_get_db_rls_extracts_workspace_id_from_jwt() -> None:
    """Vérifie que get_db_rls lit workspace_id depuis le payload JWT.

    Test statique : on inspecte le code source plutôt que d'appeler
    la dependency (qui nécessite une session DB réelle).
    """
    from pathlib import Path

    source = Path("src/gsie_api/infrastructure/database.py").read_text(encoding="utf-8")

    assert "workspace_id" in source
    assert "app.current_workspace_id" in source
    assert 'user.get("workspace_id")' in source
