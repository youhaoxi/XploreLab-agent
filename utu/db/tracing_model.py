from typing import Optional, Any, Dict, Mapping, Sequence, Literal

# from agents.tracing import FunctionSpanData, GenerationSpanData
from sqlalchemy import JSON
from sqlmodel import SQLModel, Field, Column, String


# FunctionSpanData
class ToolTracingModel(SQLModel, table=True):
    __tablename__ = "tracing_tool"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    trace_id: str = ""
    span_id: str = ""

    name: str = ""
    input: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    output: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    mcp_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))


# GenerationSpanData
class GenerationTracingModel(SQLModel, table=True):
    __tablename__ = "tracing_generation"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    trace_id: str = ""
    span_id: str = ""
    type: Literal["chat.completions", "responses"] = Field(default="chat.completions", sa_column=Column(String))

    input: Optional[Sequence[Mapping[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    output: Optional[Sequence[Mapping[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    model: str = Field(sa_column=Column(String))
    model_configs: Optional[Mapping[str, Any]] = Field(default=None, sa_column=Column(JSON))
    usage: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    response_id: Optional[str] = Field(default=None, sa_column=Column(String))
