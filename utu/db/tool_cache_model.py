from typing import Optional, Any

from sqlalchemy import JSON
from sqlmodel import SQLModel, Field, Column, String, Float


class ToolCacheModel(SQLModel, table=True):
    __tablename__ = "cache_tool"

    id: Optional[int] = Field(default=None, primary_key=True)

    function: str = Field(sa_column=Column(String))
    args: Optional[str] = Field(default=None, sa_column=Column(String))
    kwargs: Optional[str] = Field(default=None, sa_column=Column(String))
    result: Optional[Any] = Field(default=None, sa_column=Column(JSON))

    cache_key: str = Field(sa_column=Column(String))
    timestamp: int = Field(sa_column=Column(Float))
    datetime: str = Field(sa_column=Column(String))
    execution_time: float = Field(sa_column=Column(Float))
