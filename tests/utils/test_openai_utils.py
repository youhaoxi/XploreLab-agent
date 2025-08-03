from utu.utils import SimplifiedAsyncOpenAI, OpenAIUtils
from utu.config import ConfigLoader


config = ConfigLoader.load_model_config("base")
openai_client = SimplifiedAsyncOpenAI(**config.model_provider.model_dump())
print(f"Testing {config.model_provider.model}, with api_key={config.model_provider.api_key[:5]}..., base_url={config.model_provider.base_url}")
# messages = [{"role": "user", "content": "Tell a joke. And what is the weather like in Bogotá and Shanghai?"}]
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

async def test_model():
    res = await openai_client.chat_completion(messages=messages, tools=tools, stream=False)
    print(res.choices[0].message)

async def test_model_stream():
    stream = await openai_client.chat_completion(messages=messages, tools=tools, stream=True)
    async for chunk in stream:
        print(chunk.choices[0].delta)


async def test_print():
    res = await openai_client.chat_completion(messages=messages, tools=tools, stream=False)
    OpenAIUtils.print_message(res.choices[0].message)

async def test_print_stream():
    stream = await openai_client.chat_completion(messages=messages, tools=tools, stream=True)
    message = await OpenAIUtils.print_stream(stream)
    print()
    print(message)
    print()


# test extra bodys
async def test_retry():
    res = await openai_client.chat_completion(messages=messages, tools=tools, stream=False,
        # manually trigger retry with 500 (internal server error)
        extra_body={
            "return_status_code": 500,
            "enable_format_check": True
        }
    )
    print(res)

async def test_parallel_tool_calls():
    res = await openai_client.chat_completion(messages=messages, tools=tools, stream=False,
        # manually trigger retry with 500 (internal server error)
        extra_body={
            "parallel_tool_calls": False
        }
    )
    print(res)
