"""Rate limiter global — partagé entre tous les routers.

Définit le Limiter avec storage_uri Redis (configuré dans Settings) pour
garantir la distribution entre workers Gunicorn. Les routers importent
ce module au lieu d'instancier leur propre Limiter (qui serait memory://).
"""

from ipaddress import ip_address

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from gsie_api.core.config import get_settings

_settings = get_settings()


def get_client_address(request: Request) -> str:
    """Retourne une adresse canonique sans faire confiance au client direct.

    ``CF-Connecting-IP`` n'est pris en compte que lorsque l'exploitation a
    explicitement activé Cloudflare Tunnel. Dans ce mode, le port de l'API
    reste lié à la boucle locale et l'origine n'est pas publiée directement.
    Une valeur absente ou mal formée retombe sur l'adresse du pair réseau.
    """
    if _settings.edge_proxy_mode == "cloudflare_tunnel":
        forwarded = request.headers.get("CF-Connecting-IP")
        if forwarded:
            try:
                return str(ip_address(forwarded.strip()))
            except ValueError:
                pass
    return get_remote_address(request)


# `key_style="endpoint"` est indispensable : par défaut slowapi compte le quota
# par URL *concrète*. Sur une route paramétrée (`/resources/{id}`), changer
# d'identifiant remettait donc le compteur à zéro et la limite de 10 DELETE par
# minute ne bornait rien du tout. La clé devient ici le nom de la fonction de
# route, stable quel que soit l'identifiant appelé.
limiter = Limiter(
    key_func=get_client_address,
    enabled=_settings.rate_limit_enabled,
    storage_uri=_settings.rate_limit_storage_url,
    headers_enabled=True,
    key_style="endpoint",
)
