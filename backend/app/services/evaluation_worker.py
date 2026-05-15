import asyncio
import logging
import random
import uuid
from datetime import datetime, timezone

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.models.enums import RiskEvaluationStatus, RiskLevel
from app.models.risk_evaluation import RiskEvaluation

logger = logging.getLogger(__name__)


def _score_to_risk_level(score: float) -> RiskLevel:
    if score < 33:
        return RiskLevel.LOW
    if score < 67:
        return RiskLevel.MEDIUM
    return RiskLevel.HIGH


async def run_risk_evaluation(evaluation_id: uuid.UUID) -> None:
    """Simulated slow evaluation; runs outside the HTTP request."""
    await asyncio.sleep(settings.RISK_EVALUATION_DELAY_SECONDS)

    async with AsyncSessionLocal() as session:
        ev = await session.get(RiskEvaluation, evaluation_id)
        if ev is None:
            logger.warning("Risk evaluation %s not found", evaluation_id)
            return
        if ev.status != RiskEvaluationStatus.PENDING:
            logger.info(
                "Skipping evaluation %s (status=%s)",
                evaluation_id,
                ev.status,
            )
            return

        ev.status = RiskEvaluationStatus.IN_PROGRESS
        await session.flush()

        try:
            score = random.uniform(0, 100)
            ev.score = round(score, 2)
            ev.risk_level = _score_to_risk_level(score)
            ev.details = {"engine": "simulated", "version": "1"}
            ev.status = RiskEvaluationStatus.COMPLETED
            ev.completed_at = datetime.now(timezone.utc)
        except Exception as exc:
            logger.exception("Risk evaluation %s failed", evaluation_id)
            ev.status = RiskEvaluationStatus.FAILED
            ev.error_message = str(exc)[:2000]
            ev.completed_at = datetime.now(timezone.utc)

        await session.commit()
