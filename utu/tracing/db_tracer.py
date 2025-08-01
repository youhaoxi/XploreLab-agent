""" 
useful: 
    get_current_span, get_current_trace
    add_trace_processor
"""
import os
from typing import Any

from agents.tracing import Span, Trace, TracingProcessor, get_current_trace
from agents.tracing.span_data import (
    AgentSpanData,
    CustomSpanData,
    FunctionSpanData,
    GenerationSpanData,
    GuardrailSpanData,
    HandoffSpanData,
    ResponseSpanData,
    SpanData,
)
from sqlmodel import create_engine, Session, SQLModel

from ..db import ToolTracingModel, GenerationTracingModel


class DBTracingProcessor(TracingProcessor):
    def __init__(self) -> None:
        self.engine = create_engine(os.getenv("DB_URL"), pool_size=300, max_overflow=500, pool_timeout=30)
        SQLModel.metadata.create_all(self.engine)

    def on_trace_start(self, trace: "Trace") -> None:
        pass

    def on_trace_end(self, trace: "Trace") -> None:
        pass

    def on_span_start(self, span: Span[Any]) -> None:
        pass

    def on_span_end(self, span: Span[Any]) -> None:
        data = span.span_data
        if isinstance(data, GenerationSpanData):
            with Session(self.engine) as session:
                session.add(GenerationTracingModel(
                    trace_id=get_current_trace().trace_id,
                    span_id=span.span_id,
                    input=data.input,
                    output=data.output,
                    model=data.model,
                    model_configs=data.model_config,
                    usage=data.usage,
                ))
                session.commit()
        elif isinstance(data, FunctionSpanData):
            with Session(self.engine) as session:
                session.add(ToolTracingModel(
                    name=data.name,
                    input=data.input,
                    output=data.output,
                    mcp_data=data.mcp_data,
                    trace_id=get_current_trace().trace_id,
                    span_id=span.span_id,
                ))
                session.commit()

    def force_flush(self) -> None:
        pass
    def shutdown(self) -> None:
        pass
