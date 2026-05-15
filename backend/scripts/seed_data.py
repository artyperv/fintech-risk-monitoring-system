#!/usr/bin/env python3
"""One-shot demo data: clears tables and inserts sample businesses + evaluations.

  PYTHONPATH=. python scripts/seed_data.py
  docker compose exec backend python scripts/seed_data.py
"""

import asyncio
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.core.db import AsyncSessionLocal, engine
from app.models.business import Business
from app.models.enums import RiskEvaluationStatus, RiskLevel
from app.models.risk_evaluation import RiskEvaluation

# First entries are newest (list sort: created_at desc) and get longer history.
HISTORY_LONG = (90, 60, 45, 30, 21, 14, 7, 3)
HISTORY_DEFAULT = (30, 14, 3)

BUSINESSES = [
    ("Acme Payments", "fintech"),
    ("Northstar Lending", "lending"),
    ("Blue Harbor Capital", "payments"),
    ("Summit Trading", "crypto"),
    ("Vertex Insurance", "insurance"),
    ("Pioneer Wealth", "wealth management"),
    ("Atlas Regtech", "regtech"),
    ("Horizon Commerce", "e-commerce"),
    ("Cedar Finance", "fintech"),
    ("Nova Credit", "lending"),
    ("Meridian Holdings", "payments"),
    ("Silverline Partners", None),
    ("Ironclad Labs", "regtech"),
    ("Clearwater Group", "insurance"),
    ("Brightpath Capital", "fintech"),
]


def _risk_level(score: float) -> RiskLevel:
    if score < 33:
        return RiskLevel.LOW
    if score < 67:
        return RiskLevel.MEDIUM
    return RiskLevel.HIGH


async def main() -> None:
    rng = random.Random(42)
    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as session:
        await session.execute(text("TRUNCATE risk_evaluation, business CASCADE"))

        for index, (name, industry) in enumerate(BUSINESSES):
            business = Business(
                name=name,
                industry=industry,
                created_at=now - timedelta(days=index),
            )
            session.add(business)
            await session.flush()

            history_days = HISTORY_LONG if index < 4 else HISTORY_DEFAULT
            for days_ago in history_days:
                score = round(rng.uniform(10, 95), 2)
                completed = now - timedelta(days=days_ago)
                session.add(
                    RiskEvaluation(
                        business_id=business.id,
                        status=RiskEvaluationStatus.COMPLETED,
                        score=score,
                        risk_level=_risk_level(score),
                        details={"engine": "simulated", "version": "1"},
                        requested_at=completed - timedelta(minutes=5),
                        completed_at=completed,
                    )
                )

            if name in ("Acme Payments", "Summit Trading"):
                session.add(
                    RiskEvaluation(
                        business_id=business.id,
                        status=RiskEvaluationStatus.PENDING,
                        details={"engine": "simulated", "version": "1"},
                    )
                )

        await session.commit()

    await engine.dispose()
    print(f"Seeded {len(BUSINESSES)} businesses with risk history.")


if __name__ == "__main__":
    asyncio.run(main())
