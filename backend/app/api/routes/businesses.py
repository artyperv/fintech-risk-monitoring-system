import asyncio
import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import SessionDep
from app.crud import businesses as business_crud
from app.crud import risk_evaluations as risk_crud
from app.models.enums import RiskEvaluationStatus, RiskLevel
from app.models.risk_evaluation import RiskEvaluation
from app.schemas.business import (
    BusinessCreate,
    BusinessDetailRead,
    BusinessListPage,
    BusinessRead,
    LatestCompletedRisk,
    PendingEvaluationSummary,
    RiskEvaluationRead,
    RiskHistoryPage,
    TriggerEvaluateResponse,
)
from app.services.evaluation_worker import run_risk_evaluation

router = APIRouter(prefix="/businesses", tags=["businesses"])

_NOT_FOUND = {404: {"description": "Business not found"}}
_CONFLICT = {409: {"description": "Risk evaluation already in progress"}}


@router.post(
    "",
    response_model=BusinessRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_business_route(
    body: BusinessCreate,
    session: SessionDep,
) -> BusinessRead:
    business = await business_crud.create_business(session, body)
    await session.commit()
    await session.refresh(business)
    return business


@router.get("", response_model=BusinessListPage)
async def list_businesses_route(
    session: SessionDep,
    name: str | None = Query(default=None, description="Case-insensitive substring match"),
    risk_level: RiskLevel | None = Query(
        default=None,
        description="Filter by latest completed evaluation risk factor (low, medium, high)",
    ),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> BusinessListPage:
    businesses, total = await business_crud.list_businesses(
        session,
        name_contains=name,
        risk_level=risk_level,
        skip=skip,
        limit=limit,
    )
    return BusinessListPage(
        items=[BusinessRead.model_validate(b) for b in businesses],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{business_id}/risk-history",
    response_model=RiskHistoryPage,
    responses=_NOT_FOUND,
)
async def risk_history(
    business_id: uuid.UUID,
    session: SessionDep,
    evaluation_status: RiskEvaluationStatus | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> RiskHistoryPage:
    business = await business_crud.get_business(session, business_id)
    if business is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Business not found")

    items, total = await risk_crud.list_evaluations_for_business(
        session,
        business_id,
        status=evaluation_status,
        skip=skip,
        limit=limit,
    )
    return RiskHistoryPage(
        items=[RiskEvaluationRead.model_validate(x) for x in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/{business_id}/evaluate",
    response_model=TriggerEvaluateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={**_NOT_FOUND, **_CONFLICT},
)
async def trigger_evaluate(
    business_id: uuid.UUID,
    session: SessionDep,
) -> TriggerEvaluateResponse:
    business = await business_crud.get_business(session, business_id)
    if business is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Business not found")

    active = await risk_crud.get_latest_active_for_business(session, business_id)
    if active is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Risk evaluation already in progress",
        )

    evaluation = await risk_crud.create_pending_evaluation(session, business_id)
    await session.commit()
    await session.refresh(evaluation)

    asyncio.create_task(run_risk_evaluation(evaluation.id))

    status_value = (
        evaluation.status.value
        if hasattr(evaluation.status, "value")
        else str(evaluation.status)
    )
    return TriggerEvaluateResponse(
        evaluation_id=evaluation.id,
        status=status_value,
    )


@router.get(
    "/{business_id}",
    response_model=BusinessDetailRead,
    responses=_NOT_FOUND,
)
async def get_business_detail(
    business_id: uuid.UUID,
    session: SessionDep,
) -> BusinessDetailRead:
    business = await business_crud.get_business(session, business_id)
    if business is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Business not found")

    latest = await risk_crud.get_latest_completed_for_business(session, business_id)
    pending = await risk_crud.get_latest_active_for_business(session, business_id)

    return BusinessDetailRead(
        id=business.id,
        name=business.name,
        industry=business.industry,
        created_at=business.created_at,
        latest_completed_risk=latest,
        pending_evaluation=pending,
    )
