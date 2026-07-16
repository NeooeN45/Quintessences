"""Rate limiter global — partagé entre tous les routers.

Définit le Limiter avec storage_uri Redis (configuré dans Settings) pour
garantir la distribution entre workers Gunicorn. Les routers importent
ce module au lieu d'instancier leur propre Limiter (qui serait memory://).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from gsie_api.core.config import get_settings

_settings = get_settings()

limiter = Limiter(
    key_func=get_remote_address,
    enabled=_settings.rate_limit_enabled,
    storage_uri=_settings.rate_limit_storage_url,
    headers_enabled=True,
)
