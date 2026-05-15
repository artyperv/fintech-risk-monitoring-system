from enum import Enum as PythonEnum


class RiskEvaluationStatus(PythonEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskLevel(PythonEnum):
    """Risk factor tier from latest completed evaluation."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
