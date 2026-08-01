"""SDK Python GSIE — client asynchrone pour l'API GSIE.

Voir README.md pour le usage et pyproject.toml pour les dépendances.
"""

from gsie_sdk.client import GSIEClient
from gsie_sdk.engines import Engines
from gsie_sdk.exceptions import APIError, AuthenticationError, GSIEError, TokenRefreshError

__all__ = [
    "GSIEClient",
    "Engines",
    "GSIEError",
    "AuthenticationError",
    "TokenRefreshError",
    "APIError",
]

__version__ = "0.1.0"
