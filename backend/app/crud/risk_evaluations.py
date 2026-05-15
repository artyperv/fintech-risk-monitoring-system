import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import RiskEvaluationStatus
from app.models.risk_evaluation import RiskEvaluation


async def create_pending_evaluation(
    session: AsyncSession,
    business_id: uuid.UUID,
) -> RiskEvaluation:
    evaluation = RiskEvaluation(
        business_id=business_id,
        status=RiskEvaluationStatus.PENDING,
    )
    session.add(evaluation)
    await session.flush()
    await session.refresh(evaluation)
    return evaluation


async def get_evaluation(
    session: AsyncSession, evaluation_id: uuid.UUID
) -> RiskEvaluation | None:
    return await session.get(RiskEvaluation, evaluation_id)


async def get_latest_completed_for_business(
    session: AsyncSession, business_id: uuid.UUID
) -> RiskEvaluation | None:
    stmt = (
        select(RiskEvaluation)
        .where(
            RiskEvaluation.business_id == business_id,
            RiskEvaluation.status == RiskEvaluationStatus.COMPLETED,
            RiskEvaluation.completed_at.isnot(None),
        )
        .order_by(RiskEvaluation.completed_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_latest_pending_for_business(
    session: AsyncSession, business_id: uuid.UUID
) -> RiskEvaluation | None:
    return await get_latest_active_for_business(session, business_id)


async def get_latest_active_for_business(
    session: AsyncSession, business_id: uuid.UUID
) -> RiskEvaluation | None:
    active_statuses = (
        RiskEvaluationStatus.PENDING,
        RiskEvaluationStatus.IN_PROGRESS,
    )
    stmt = (
        select(RiskEvaluation)
        .where(
            RiskEvaluation.business_id == business_id,
            RiskEvaluation.status.in_(active_statuses),
        )
        .order_by(RiskEvaluation.requested_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def list_evaluations_for_business(
    session: AsyncSession,
    business_id: uuid.UUID,
    status: RiskEvaluationStatus | None,
    skip: int,
    limit: int,
) -> tuple[list[RiskEvaluation], int]:
    stmt = select(RiskEvaluation).where(RiskEvaluation.business_id == business_id)
    count_stmt = select(func.count()).select_from(RiskEvaluation).where(
        RiskEvaluation.business_id == business_id
    )

    if status is not None:
        stmt = stmt.where(RiskEvaluation.status == status)
        count_stmt = count_stmt.where(RiskEvaluation.status == status)

    stmt = stmt.order_by(RiskEvaluation.requested_at.desc()).offset(skip).limit(limit)

    result = await session.execute(stmt)
    items = list(result.scalars().all())

    total_result = await session.execute(count_stmt)
    total = int(total_result.scalar_one())

    return items, total
