import logging
from datetime import datetime

import pytest
from agents import Agent, Runner, function_tool

from utu.utils import AgentsUtils


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
