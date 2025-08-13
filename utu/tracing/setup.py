"""
open-inference: https://github.com/Arize-ai/openinference
https://github.com/Arize-ai/openinference/tree/main/python/instrumentation/openinference-instrumentation-openai-agents
TODO: rewrite openinference-instrumentation-openai-agents to support
    1. session-level tracing in @phoenix https://arize.com/docs/phoenix/tracing/how-to-tracing/setup-tracing/setup-sessions
    ref: test_tracing.py
"""

import os
import warnings

from agents import add_trace_processor
from openinference.instrumentation.openai import OpenAIInstrumentor
from phoenix.otel import TracerProvider, register

from .db_tracer import DBTracingProcessor

# from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor
from .otel_agents_instrumentor import OpenAIAgentsInstrumentor

PHOENIX_TRACING_PROVIDER: TracerProvider | None = None
DB_TRACING_PROCESSOR: DBTracingProcessor | None = None


def setup_phoenix_tracing(
    endpoint: str = None,
    project_name: str = None,
) -> None:
    global PHOENIX_TRACING_PROVIDER
    if PHOENIX_TRACING_PROVIDER is not None:
        return
    endpoint = endpoint or os.getenv("PHOENIX_ENDPOINT")
    project_name = project_name or os.getenv("PHOENIX_PROJECT_NAME")
    if not endpoint or not project_name:
        warnings.warn("PHOENIX_ENDPOINT or PHOENIX_PROJECT_NAME is not set", stacklevel=2)
        return
    PHOENIX_TRACING_PROVIDER = register(
        endpoint=endpoint,
        project_name=project_name,
        batch=True,  # TEST: SimpleSpanProcessor may reduce performance, but BatchSpanProcessor can lead to error?
        # protocol="grpc", # grpc | http/protobuf, will automatically inferred!
        auto_instrument=False,
    )
    # manually instrument
    OpenAIInstrumentor().instrument(tracer_provider=PHOENIX_TRACING_PROVIDER)
    OpenAIAgentsInstrumentor().instrument(
        tracer_provider=PHOENIX_TRACING_PROVIDER, exclusive_processor=True
    )  # remove default tracing to openai


def setup_db_tracing() -> None:
    global DB_TRACING_PROCESSOR
    if DB_TRACING_PROCESSOR is not None:
        return
    DB_TRACING_PROCESSOR = DBTracingProcessor()
    add_trace_processor(DB_TRACING_PROCESSOR)


def setup_tracing() -> None:
    setup_phoenix_tracing()
    setup_db_tracing()
