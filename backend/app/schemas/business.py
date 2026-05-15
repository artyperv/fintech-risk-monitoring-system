from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
from sqlmodel import SQLModel


class BusinessCreate(BaseModel):
    name: str = Field(min_length=1)
    industry: str | None = None

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("industry", mode="before")
    @classmethod
    def strip_industry(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class BusinessRead(SQLModel):
    id: UUID
    name: str
    industry: str | None
    created_at: datetime


class LatestCompletedRisk(SQLModel):
    id: UUID
    score: float
    risk_level: str
    requested_at: datetime
    completed_at: datetime


class PendingEvaluationSummary(SQLModel):
    id: UUID
    requested_at: datetime


class BusinessDetailRead(BusinessRead):
    latest_completed_risk: LatestCompletedRisk | None = None
    pending_evaluation: PendingEvaluationSummary | None = None


class TriggerEvaluateResponse(SQLModel):
    evaluation_id: UUID
    status: str


class RiskEvaluationRead(SQLModel):
    id: UUID
    business_id: UUID
    status: str
    requested_at: datetime
    completed_at: datetime | None
    score: float | None
    risk_level: str | None
    details: dict | None
    error_message: str | None


class BusinessListPage(SQLModel):
    items: list[BusinessRead]
    total: int
    skip: int
    limit: int


class RiskHistoryPage(SQLModel):
    items: list[RiskEvaluationRead]
    total: int
    skip: int
    limit: int
