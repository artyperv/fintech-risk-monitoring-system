from datetime import datetime
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import event
from sqlmodel import Field, Relationship, SQLModel


if TYPE_CHECKING:
    from app.models.risk_evaluation import RiskEvaluation


class Business(SQLModel, table=True):
    __tablename__ = "business"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(nullable=False, index=True)
    industry: str | None = None

    created_at: datetime = Field(default=datetime.now, nullable=False)

    risk_evaluations: list["RiskEvaluation"] = Relationship(
        back_populates="business",
        sa_relationship_kwargs={"lazy": "noload"},
    )

@event.listens_for(Business, "before_insert", propagate=True)
def timestamp_before_insert(_mapper, _connection, target):
    target.created_at = datetime.now()
