"""Route publique de contact du site Quintessences."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from gsie_api.auth.transactional_email import (
    TransactionalEmailSender,
    get_transactional_email_sender,
)
from gsie_api.core.config import get_settings
from gsie_api.core.limiter import get_client_address, limiter
from gsie_api.core.logging import get_logger
from gsie_api.shared.turnstile import TurnstileClient, TurnstileVerificationError

from .schemas import PublicContactRequest, PublicContactResponse

router = APIRouter(prefix="/public", tags=["public"])
logger = get_logger("gsie_api.public_contact")


def get_contact_sender() -> TransactionalEmailSender:
    """Retourne le transport transactionnel configuré pour le processus."""

    return get_transactional_email_sender()


@router.post(
    "/contact",
    response_model=PublicContactResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@limiter.limit("5/minute")
async def submit_contact(
    request: Request,
    response: Response,
    payload: PublicContactRequest,
    sender: Annotated[TransactionalEmailSender, Depends(get_contact_sender)],
) -> PublicContactResponse:
    """Valide puis transmet un message sans l'enregistrer en base GSIE."""

    settings = get_settings()
    if not settings.public_contact_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Le service de contact est temporairement indisponible.",
        )

    # Champ piège : répondre positivement sans livrer le contenu évite de
    # fournir un oracle aux robots qui remplissent tous les champs.
    if payload.website:
        return PublicContactResponse()

    client_ip = get_client_address(request)
    try:
        valid_turnstile = await TurnstileClient(settings).verify(
            payload.turnstile_token,
            remote_ip=client_ip,
        )
    except TurnstileVerificationError as exc:
        logger.warning("public_contact_turnstile_unavailable", error_type=type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La vérification anti-robot est temporairement indisponible.",
        ) from exc

    if not valid_turnstile:
        logger.warning("public_contact_turnstile_rejected")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Challenge anti-robot non résolu.",
        )

    if not sender.is_configured:
        logger.error("public_contact_sender_not_configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Le service de contact est temporairement indisponible.",
        )

    delivered = await sender.send_contact(
        sender_email=str(payload.email),
        category=payload.category.value,
        message=payload.message,
    )
    if not delivered:
        logger.error("public_contact_delivery_failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Le message n'a pas pu être transmis. Écrivez directement à "
                "contact@quintessences-platform.com."
            ),
        )

    return PublicContactResponse()
