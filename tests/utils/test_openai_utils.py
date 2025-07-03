import pytest
from openai import OpenAI

from utu.utils import OpenAIUtils
from utu.config import ConfigLoader, ModelConfig


@pytest.fixture(scope="session")
def config() -> ModelConfig:
    return ConfigLoader.load_model_config("base")

@pytest.fixture(scope="session")
def openai_client(config: ModelConfig) -> OpenAI:
    client = OpenAI(base_url=config.base_url, api_key=config.api_key)
    return client

def test_print_stream(openai_client: OpenAI, config: ModelConfig):
    messages = [{"role": "user", "content": "Tell a joke. And what is the weather like in Bogotá and Shanghai?"}]
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
    stream = openai_client.chat.completions.create(
        messages=messages, tools=tools, tool_choice="required",
        model=config.model, stream=True
    )
    message = OpenAIUtils.print_stream(stream)
    print(message)
    print()
