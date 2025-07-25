""" 
open-inference: https://github.com/Arize-ai/openinference
https://github.com/Arize-ai/openinference/tree/main/python/instrumentation/openinference-instrumentation-openai-agents
TODO: rewrite openinference-instrumentation-openai-agents to support
    1. session-level tracing in @phoenix https://arize.com/docs/phoenix/tracing/how-to-tracing/setup-tracing/setup-sessions
    ref: test_tracing.py
"""
from agents import add_trace_processor
from phoenix.otel import register, TracerProvider
from openinference.instrumentation.openai import OpenAIInstrumentor
# from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor
from .otel_agents_instrumentor import OpenAIAgentsInstrumentor
from .db_tracer import DBTracingProcessor


PHOENIX_TRACING_PROVIDER = None
DB_TRACING_PROCESSOR = None

def setup_phoenix_tracing() -> None:
    """ 
    - [ ] add try-except when start phoenix
    """
    global PHOENIX_TRACING_PROVIDER
    if PHOENIX_TRACING_PROVIDER is not None: return
    PHOENIX_TRACING_PROVIDER = register(
        endpoint="http://9.134.230.111:4317",
        project_name="uTu agent",
        batch=True,
        # protocol="grpc", # grpc | http/protobuf, will automatically inferred!
        auto_instrument=False,
    )
    # manually instrument
    OpenAIInstrumentor().instrument(tracer_provider=PHOENIX_TRACING_PROVIDER)
    OpenAIAgentsInstrumentor().instrument(tracer_provider=PHOENIX_TRACING_PROVIDER)


def setup_db_tracing() -> None:
    global DB_TRACING_PROCESSOR
    if DB_TRACING_PROCESSOR is not None: return
    DB_TRACING_PROCESSOR = DBTracingProcessor()
    add_trace_processor(DB_TRACING_PROCESSOR)


def setup_tracing() -> None:
    setup_phoenix_tracing()
    setup_db_tracing()