import uuid

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business import Business
from app.models.enums import RiskEvaluationStatus, RiskLevel
from app.models.risk_evaluation import RiskEvaluation
from app.schemas.business import BusinessCreate


def _latest_completed_business_ids_subquery(risk_level: RiskLevel):
    """Business IDs whose most recent completed evaluation matches the risk level."""
    latest_completed = (
        select(
            RiskEvaluation.business_id.label("business_id"),
            func.max(RiskEvaluation.completed_at).label("max_completed_at"),
        )
        .where(RiskEvaluation.status == RiskEvaluationStatus.COMPLETED)
        .group_by(RiskEvaluation.business_id)
        .subquery()
    )

    return (
        select(RiskEvaluation.business_id)
        .join(
            latest_completed,
            and_(
                RiskEvaluation.business_id == latest_completed.c.business_id,
                RiskEvaluation.completed_at == latest_completed.c.max_completed_at,
            ),
        )
        .where(
            RiskEvaluation.status == RiskEvaluationStatus.COMPLETED,
            RiskEvaluation.risk_level == risk_level,
        )
    )


async def create_business(session: AsyncSession, data: BusinessCreate) -> Business:
    industry = (data.industry or "").strip() or None
    business = Business(
        name=data.name.strip(),
        industry=industry,
    )
    session.add(business)
    await session.flush()
    await session.refresh(business)
    return business


async def get_business(session: AsyncSession, business_id: uuid.UUID) -> Business | None:
    return await session.get(Business, business_id)


async def list_businesses(
    session: AsyncSession,
    *,
    name_contains: str | None,
    risk_level: RiskLevel | None,
    skip: int,
    limit: int,
) -> tuple[list[Business], int]:
    stmt = select(Business)
    count_stmt = select(func.count()).select_from(Business)

    if name_contains:
        pattern = f"%{name_contains.strip()}%"
        stmt = stmt.where(Business.name.ilike(pattern))
        count_stmt = count_stmt.where(Business.name.ilike(pattern))

    if risk_level is not None:
        matching_ids = _latest_completed_business_ids_subquery(risk_level)
        stmt = stmt.where(Business.id.in_(matching_ids))
        count_stmt = count_stmt.where(Business.id.in_(matching_ids))

    stmt = stmt.order_by(Business.created_at.desc()).offset(skip).limit(limit)

    result = await session.execute(stmt)
    businesses = list(result.scalars().all())

    total_result = await session.execute(count_stmt)
    total = int(total_result.scalar_one())

    return businesses, total
