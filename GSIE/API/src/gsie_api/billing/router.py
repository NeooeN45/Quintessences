"""API du catalogue et des entitlements effectifs."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.billing.schemas import (
    BillingContextResponse,
    BillingOperationResponse,
    CheckoutRequest,
    CheckoutResponse,
    EntitlementResponse,
    PlanListResponse,
    PlanResponse,
    StorePurchaseRequest,
    StorePurchaseResponse,
    UpgradeRequest,
)
from gsie_api.billing.service import BillingService, SqlAlchemyBillingRepository
from gsie_api.billing.store_gateways import (
    ApplePurchaseGateway,
    GooglePlayPurchaseGateway,
    StoreNotConfiguredError,
    StorePurchaseInvalidError,
)
from gsie_api.billing.stripe_gateway import (
    StripeBillingError,
    StripeBillingGateway,
    StripeNotConfiguredError,
    StripeWebhookError,
    StripeWebhookProcessor,
)
from gsie_api.core.auth import get_current_user
from gsie_api.core.limiter import limiter
from gsie_api.infrastructure.database import get_db, get_db_resource

router = APIRouter(prefix="/billing", tags=["billing"])


async def get_billing_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> BillingService:
    return BillingService(SqlAlchemyBillingRepository(session))


async def get_scoped_billing_service(
    session: Annotated[AsyncSession, Depends(get_db_resource)],
) -> BillingService:
    return BillingService(SqlAlchemyBillingRepository(session))


def _account_id(user: dict[str, object]) -> UUID:
    try:
        return UUID(str(user.get("sub", "")))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalide",
        ) from None


@router.get("/plans", response_model=PlanListResponse)
@limiter.limit("60/minute")
async def list_plans(
    request: Request,
    response: Response,
    service: Annotated[BillingService, Depends(get_billing_service)],
) -> PlanListResponse:
    del request, response
    plans = await service.list_public_plans()
    return PlanListResponse(
        plans=[
            PlanResponse(
                code=plan.code,
                display_name=plan.display_name,
                product_scope=plan.product_scope,
                monthly_amount_cents=plan.monthly_amount_cents,
                annual_amount_cents=plan.annual_amount_cents,
                trial_days=plan.trial_days,
                features=list(plan.features),
            )
            for plan in plans
        ]
    )


@router.post("/checkout", response_model=CheckoutResponse)
@limiter.limit("10/minute")
async def create_checkout(
    request: Request,
    response: Response,
    body: CheckoutRequest,
    user: Annotated[dict[str, object], Depends(get_current_user)],
) -> CheckoutResponse:
    del request, response
    if body.owner_type != "account":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Checkout organisation Enterprise à configurer séparément",
        )
    owner_id = _account_id(user)
    try:
        url = await StripeBillingGateway().create_checkout_session(
            plan_code=body.plan_code,
            owner_type=body.owner_type,
            owner_id=owner_id,
        )
    except StripeNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return CheckoutResponse(checkout_url=url)


@router.post("/portal", response_model=CheckoutResponse)
@limiter.limit("10/minute")
async def create_billing_portal(
    request: Request,
    response: Response,
    user: Annotated[dict[str, object], Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_resource)],
) -> CheckoutResponse:
    del response
    account_id = _account_id(user)
    organisation_raw = request.headers.get("X-Organisation-Id") or user.get("active_organisation")
    try:
        organisation_id = UUID(str(organisation_raw)) if organisation_raw else None
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organisation active invalide",
        ) from None
    from gsie_api.infrastructure.models.billing import SubscriptionModel

    conditions = [
        SubscriptionModel.provider == "stripe",
        SubscriptionModel.status.in_(("trialing", "active", "past_due")),
    ]
    conditions.append(
        SubscriptionModel.organisation_id == organisation_id
        if organisation_id is not None
        else SubscriptionModel.account_id == account_id
    )
    subscription = (
        await session.execute(select(SubscriptionModel).where(*conditions).limit(1))
    ).scalar_one_or_none()
    if subscription is None or not subscription.provider_customer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun client Stripe actif",
        )
    try:
        url = await StripeBillingGateway().create_portal_session(subscription.provider_customer_id)
    except StripeNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return CheckoutResponse(checkout_url=url)


@router.post("/upgrade", response_model=BillingOperationResponse)
@limiter.limit("5/minute")
async def upgrade_billing_plan(
    request: Request,
    response: Response,
    body: UpgradeRequest,
    user: Annotated[dict[str, object], Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_resource)],
) -> BillingOperationResponse:
    del request, response
    account_id = _account_id(user)
    from gsie_api.infrastructure.models.billing import SubscriptionModel

    subscription = (
        await session.execute(
            select(SubscriptionModel)
            .where(
                SubscriptionModel.account_id == account_id,
                SubscriptionModel.provider == "stripe",
                SubscriptionModel.status.in_(("trialing", "active", "past_due")),
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if subscription is None or not subscription.external_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun abonnement Stripe individuel actif",
        )
    if body.target_plan_code != "quintessences_pro":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upgrade non supporté",
        )
    try:
        await StripeBillingGateway().upgrade_subscription(
            subscription.external_subscription_id,
            body.target_plan_code,
        )
    except (StripeNotConfiguredError, StripeBillingError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return BillingOperationResponse()


@router.post("/purchases/google-play", response_model=StorePurchaseResponse)
@limiter.limit("10/minute")
async def validate_google_play_purchase(
    request: Request,
    response: Response,
    body: StorePurchaseRequest,
    user: Annotated[dict[str, object], Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> StorePurchaseResponse:
    del request, response
    service = BillingService(SqlAlchemyBillingRepository(session))
    try:
        purchase = await GooglePlayPurchaseGateway().verify_subscription(body.purchase_token)
        await service.apply_verified_purchase("account", _account_id(user), purchase)
        await session.commit()
    except StoreNotConfiguredError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except StorePurchaseInvalidError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return StorePurchaseResponse(
        provider=purchase.provider,
        plan_code=purchase.plan_code,
        status=purchase.status,
        expires_at=purchase.expires_at,
    )


@router.post("/purchases/apple", response_model=StorePurchaseResponse)
@limiter.limit("10/minute")
async def validate_apple_purchase(
    request: Request,
    response: Response,
    body: StorePurchaseRequest,
    user: Annotated[dict[str, object], Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> StorePurchaseResponse:
    del request, response
    service = BillingService(SqlAlchemyBillingRepository(session))
    try:
        purchase = await ApplePurchaseGateway().verify_subscription(body.purchase_token)
        await service.apply_verified_purchase("account", _account_id(user), purchase)
        await session.commit()
    except StoreNotConfiguredError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except StorePurchaseInvalidError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return StorePurchaseResponse(
        provider=purchase.provider,
        plan_code=purchase.plan_code,
        status=purchase.status,
        expires_at=purchase.expires_at,
    )


@router.post("/webhooks/stripe", status_code=status.HTTP_204_NO_CONTENT)
async def stripe_webhook(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    payload = await request.body()
    signature = request.headers.get("Stripe-Signature")
    processor = StripeWebhookProcessor(session)
    try:
        await session.execute(text("SELECT set_config('app.billing_webhook', 'true', true)"))
        event = processor.parse_event(payload, signature)
        await processor.process(event)
        await session.commit()
    except StripeWebhookError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook Stripe invalide",
        ) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/context", response_model=BillingContextResponse)
@limiter.limit("60/minute")
async def get_billing_context(
    request: Request,
    response: Response,
    user: Annotated[dict[str, object], Depends(get_current_user)],
    service: Annotated[BillingService, Depends(get_scoped_billing_service)],
) -> BillingContextResponse:
    del response
    account_id = _account_id(user)
    organisation_raw = request.headers.get("X-Organisation-Id") or user.get("active_organisation")
    try:
        organisation_id = UUID(str(organisation_raw)) if organisation_raw else None
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organisation active invalide",
        ) from None
    entitlements = await service.get_effective_entitlements(account_id, organisation_id)
    return BillingContextResponse(
        account_id=account_id,
        organisation_id=organisation_id,
        features=sorted({item.feature_code for item in entitlements}),
        entitlements=[
            EntitlementResponse(
                feature_code=item.feature_code,
                subject_type=item.subject_type,
                subject_id=item.subject_id,
                status=item.status,
                valid_until=item.valid_until,
            )
            for item in entitlements
        ],
    )
