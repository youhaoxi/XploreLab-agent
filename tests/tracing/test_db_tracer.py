from agents.tracing import agent_span, function_span, generation_span
from agents._run_impl import TraceCtxManager

from utu.tracing import setup_db_tracing

setup_db_tracing()


async def mock_function():
    with function_span(
        name="mock_function",
        input={"input": "mock_function_input"},  # "mock_function_input"
    ) as span:
        span.span_data.output = {"output": "mock_function_output"}

async def test_function_span():
    with TraceCtxManager(
        workflow_name="test_db_tracer",
        trace_id="trace_db_tracer",
        group_id="trace_db_tracer",
        metadata={"test": "test"},
        disabled=False,
    ):
        await mock_function()
