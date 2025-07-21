from utu.utils import SimplifiedAsyncOpenAI, OpenAIUtils
from utu.config import ConfigLoader


async def test_print_stream():
    config = ConfigLoader.load_model_config("v00")
    openai_client = SimplifiedAsyncOpenAI(**config.model_dump())
    print(f"Testing {config.model}, with api_key={config.api_key[:5]}..., base_url={config.base_url}")
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
    stream = await openai_client.chat_completion(messages=messages, tools=tools, stream=True)
    message = await OpenAIUtils.print_stream(stream)
    print()
    print(message)
    print()
