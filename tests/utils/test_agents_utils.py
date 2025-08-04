import os
import logging
from datetime import datetime

import pytest
from openai import AsyncOpenAI
from agents import Agent, Runner, function_tool, trace

from utu.utils.agents_utils import AgentsUtils, SimplifiedOpenAIChatCompletionsModel


@pytest.fixture
def agent() -> Agent:
    @function_tool
    def get_weather(city: str, date: str) -> str:
        """Get the weather in a city.

        Args:
            city (str): The city to get the weather for.
            date (str): The date to get the weather for. In the format of "YYYY-MM-DD".
        """
        logging.info(f"> calling tool: get_weather({city}, {date})")
        return f"The weather in {city} at {date} is sunny."

    model = AgentsUtils.get_agents_model(model="gpt-4o")
    sp = f"You are a helpful assistant. The date of today is {datetime.now().strftime('%Y-%m-%d (%A)')}."
    logging.info(f"> {sp}")
    agent = Agent(
        name="General Assistant", 
        instructions=sp, 
        model=model,
        tools=[get_weather],
    )
    return agent


async def test_print_stream_events(agent: Agent):
    stream = Runner.run_streamed(agent, "tell me a joke. And what is the weather like in Shanghai?")
    await AgentsUtils.print_stream_events(stream.stream_events())

async def test_print_events(agent: Agent):
    result = await Runner.run(agent, "tell me a joke. And what is the weather like in Shanghai?")
    AgentsUtils.print_new_items(result.new_items)


messages = [{"role": "user", "content": "给我讲两个笑话, 然后帮我查一下北京天津的天气"}]
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current temperature for a given location.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City and country e.g. Bogotá, Colombia"
                }
            },
            "required": ["location"],
            "additionalProperties": False
        },
        "strict": True
    }
}]

async def test_simplified_openai_chat_completions_model():
    model = os.getenv("UTU_MODEL")
    api_key = os.getenv("UTU_API_KEY")
    base_url = os.getenv("UTU_BASE_URL")
    openai_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    simplified_openai_model = SimplifiedOpenAIChatCompletionsModel(model=model, openai_client=openai_client)
    with trace(workflow_name="test_agent") as trace_ctx:
        res = await simplified_openai_model.query_one(messages=messages, tools=tools, model=model)
        print(res)
