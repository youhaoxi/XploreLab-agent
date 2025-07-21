from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SQLField


class UTUBaseModel(BaseModel):
    def update(self, **kwargs):
        """
        Update the evaluation sample with the given keyword arguments.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get(self, key, default=None):
        """
        Get the value of the specified key, or return default if not found.
        """
        return getattr(self, key, default)

    @classmethod
    def from_dict(cls, data: dict):
        """
        Create an EvaluationSample from a dictionary.
        """
        return cls(**data)

    def as_dict(self) -> dict:
        # only contain fields that are not None
        return {k: v for k, v in self.model_dump().items() if v is not None}


# @dataclass
class EvaluationSample(UTUBaseModel, SQLModel, table=True):
    __tablename__ = 'evaluation_data'
    
    id: Optional[int] = SQLField(default=None, primary_key=True)
    created_at: Optional[datetime] = SQLField(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = SQLField(default_factory=datetime.utcnow)

    # 1) base info
    source: str = ""  # dataset name
    raw_question: str = ""
    level: Optional[int] = 0  # hardness level of the question, if applicable
    augmented_question: Optional[str] = ""
    correct_answer: Optional[str] = ""
    file_name: Optional[str] = ""  # for GAIA
    stage: str = "init"  # Literal["init", "rollout", "judged]
    # 2) rollout
    trace_id: Optional[str] = Field(default=None)
    response: Optional[str] = Field(default=None)
    time_cost: Optional[float] = Field(default=None)  # time cost in seconds
    trajectory: Optional[str] = Field(default=None)  # the agent's reasoning process, a list of messages
    # 3) judgement
    extracted_final_answer: Optional[str] = Field(default=None)
    judged_response: Optional[str] = Field(default=None)
    reasoning: Optional[str] = Field(default=None)
    correct: Optional[bool] = Field(default=None)
    confidence: Optional[int] = Field(default=None)
    # id
    exp_id: str = Field(default="default")

    def model_dump(self, *args, **kwargs):
        keys = [
            "source", "raw_question", "level", "augmented_question", "correct_answer", "file_name", "stage", "trace_id", "response",
            "time_cost", "trajectory", "extracted_final_answer", "judged_response", "reasoning", "correct", "confidence",
            "exp_id"
        ]
        return {
            k: getattr(self, k) for k in keys if getattr(self, k) is not None
        }

class EvaluationResult(UTUBaseModel):
    """
    A data class to represent the result of an evaluation.
    """
    benchmark: str
    metrics: dict
