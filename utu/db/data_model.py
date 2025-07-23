from typing import Optional, Any

from sqlmodel import SQLModel, Field, JSON, Column


class EvaluationData(SQLModel, table=True):
    __tablename__ = 'data'
    
    id: Optional[int] = Field(default=None, primary_key=True)
    dataset: str = ""  # dataset name
    source: str = ""  # dataset name for mixed dataset

    question: str = ""
    answer: Optional[str] = ""
    topic: Optional[str] = ""  # single or multiple tags?
    level: Optional[str] = ""
    file_name: Optional[str] = ""  # for GAIA

    meta: Optional[Any] = Field(default=None, sa_column=Column(JSON))  # e.g. annotator_metadata in GAIA, extra_info in WebWalker
