
from agents import Agent
from agents.tracing import trace, agent_span, AgentSpanData, response_span, generation_span, GenerationSpanData

async def test_trace(agent: Agent):
    # FIXME: setup session_id in Phoenix
    with trace(workflow_name="test_agent") as trace_ctx:
        with agent_span("agent_span") as span:
            # FIXME: setup input/output in Phoenix
            span.span_data.input = "tell me a joke. And what is the weather like in Shanghai?"
            span.span_data.output = "final output"

