""" 
open-inference: https://github.com/Arize-ai/openinference
https://github.com/Arize-ai/openinference/tree/main/python/instrumentation/openinference-instrumentation-openai-agents
TODO: rewrite openinference-instrumentation-openai-agents to support
    1. session-level tracing in @phoenix https://arize.com/docs/phoenix/tracing/how-to-tracing/setup-tracing/setup-sessions
    ref: test_tracing.py
"""

from phoenix.otel import register, TracerProvider
from openinference.instrumentation.openai import OpenAIInstrumentor
# from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor
from .otel_agents_instrumentor import OpenAIAgentsInstrumentor

def setup_phoenix_tracing() -> TracerProvider:
    """ 
    TODO: add try-except when start phoenix
    """
    tracer_provider = register(
        endpoint="http://9.134.230.111:4317",
        project_name="uTu agent",
        batch=True,
        # protocol="grpc", # grpc | http/protobuf, will automatically inferred!
        auto_instrument=False,
    )
    # manually instrument
    OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)
    OpenAIAgentsInstrumentor().instrument(tracer_provider=tracer_provider)
    return tracer_provider
