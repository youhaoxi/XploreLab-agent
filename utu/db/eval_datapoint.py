from datetime import datetime
from typing import Any, Optional

from sqlmodel import JSON, Column, Field, SQLModel

from .utu_basemodel import UTUBaseModel


class DatasetSample(SQLModel, table=True):
    __tablename__ = "data"

    id: Optional[int] = Field(default=None, primary_key=True)
    dataset: str = ""  # dataset name, for exp
    index: Optional[int] = Field(default=None)  # The index of the datapoint in the dataset, starting from 1
    source: str = ""  # dataset name for mixed dataset
    source_index: Optional[int] = Field(default=None)  # The index of the datapoint in the source dataset, if available

    question: str = ""
    answer: Optional[str] = ""
    topic: Optional[str] = ""
    level: Optional[str] = ""
    file_name: Optional[str] = ""  # for GAIA

    meta: Optional[Any] = Field(
        default=None, sa_column=Column(JSON)
    )  # e.g. annotator_metadata in GAIA, extra_info in WebWalker


class EvaluationSample(UTUBaseModel, SQLModel, table=True):
    __tablename__ = "evaluation_data"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # 1) base info
    dataset: str = ""  # dataset name
    dataset_index: Optional[int] = Field(default=None)
    source: str = ""
    raw_question: str = ""
    level: Optional[int] = 0  # hardness level of the question, if applicable
    augmented_question: Optional[str] = ""
    correct_answer: Optional[str] = ""
    file_name: Optional[str] = ""  # for GAIA
    meta: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    # 2) rollout
    trace_id: Optional[str] = Field(default=None)
    trace_url: Optional[str] = Field(default=None)
    response: Optional[str] = Field(default=None)
    time_cost: Optional[float] = Field(default=None)  # time cost in seconds
    trajectory: Optional[str] = Field(default=None)  # deprecated, use trajectories instead for multi-agents
    trajectories: Optional[str] = Field(default=None)
    # 3) judgement
    extracted_final_answer: Optional[str] = Field(default=None)
    judged_response: Optional[str] = Field(default=None)
    reasoning: Optional[str] = Field(default=None)
    correct: Optional[bool] = Field(default=None)
    confidence: Optional[int] = Field(default=None)
    # id
    exp_id: str = Field(default="default")
    stage: str = "init"  # Literal["init", "rollout", "judged]

    def model_dump(self, *args, **kwargs):
        keys = [
            "exp_id",
            "dataset",
            "dataset_index",
            "source",
            "level",
            "raw_question",
            "correct_answer",
            "file_name",
            "stage",
            "trace_id",
            "response",
            "time_cost",
            "trajectory",
            "trajectories",
            "judged_response",
            "correct",
            "confidence",
        ]
        return {k: getattr(self, k) for k in keys if getattr(self, k) is not None}
