"""WebSocket package — temps réel pour le Hub et les apps."""

from gsie_api.websocket.events import EventType, WSEvent
from gsie_api.websocket.manager import ConnectionManager, manager
from gsie_api.websocket.router import router as ws_router

__all__ = [
    "ws_router",
    "ConnectionManager",
    "manager",
    "EventType",
    "WSEvent",
]
