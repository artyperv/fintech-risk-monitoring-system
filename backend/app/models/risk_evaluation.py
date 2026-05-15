import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import event
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from app.models.enums import RiskEvaluationStatus, RiskLevel

if TYPE_CHECKING:
    from app.models.business import Business


class RiskEvaluation(SQLModel, table=True):
    __tablename__ = "risk_evaluation"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    business_id: uuid.UUID = Field(foreign_key="business.id", nullable=False, index=True)
    status: RiskEvaluationStatus = Field(default=RiskEvaluationStatus.PENDING, index=True)

    score: float | None = None
    risk_level: RiskLevel | None = None
    details: dict = Field(default_factory=dict, sa_type=JSONB)
    error_message: str | None = None

    requested_at: datetime = Field(default=datetime.now, nullable=False)
    completed_at: datetime | None = None

    business: "Business" = Relationship(
        back_populates="risk_evaluations",
        sa_relationship_kwargs={"lazy": "noload"},
    )

@event.listens_for(RiskEvaluation, "before_insert", propagate=True)
def timestamp_before_insert(_mapper, _connection, target):
    target.requested_at = datetime.now()