""" Standalone test for ReAct mode (ReactConverter)
> see final version in [test_react_model.py]
"""
import json
import asyncio
import jinja2
from openai.types.chat import (
    ChatCompletionToolParam,
    ChatCompletionMessageParam,
    ChatCompletion,
)
from utu.utils import SimplifiedAsyncOpenAI

simplified_openai = SimplifiedAsyncOpenAI()
jinja_env = jinja2.Environment()


tools: dict[str, ChatCompletionToolParam] = {
    "get_time": {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Get the current time",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "The timezone to get the time in"
                    }
                },
                "required": ["timezone"]
            }
        }
    },

    "search_google_api": {
        "type": "function",
        "function": {
            "name": "search_google_api",
            "description": "Search the query via Google api, the query should be a search query like humans search in Google, concrete and not vague or super long. More the single most important items.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to search for."
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "The number of results to return. Defaults to 20."
                    }
                },
                "required": ["query"]
            }
        }
    },
    "web_qa": {
        "type": "function",
        "function": {
            "name": "web_qa",
            "description": "Query information you interested from the specified url",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The url to get content from."
                    },
                    "query": {
                        "type": "string",
                        "description": "The query to search for. If not given, return the original content of the url."
                    }
                },
                "required": ["url"]
            }
        }
    }
}

tasks_single = [
    {
        "messages": [{"role": "user", "content": "What's the time now in Shanghai?"}],
        "tools": [tools["get_time"]]
    }
]
tasks_multi = [
    {
        "messages": [
            {"role": "user", "content": "Introduce the smolagents package."},
            {"role": "assistant", "content": "", "tool_calls": [
                {"id": "0", "type": "function", "function": {"name": "search_google_api", "arguments": str({"query": "smolagents package"})}}
            ]},
            {"role": "tool", "tool_call_id": "0", "content": str({"results": [
                {"id": "0", "title": "smolagents: a barebones library for agents that think in code.", "url": "https://github.com/huggingface/smolagents/"},
                {"id": "1", "title": "smolagents", "url": "https://huggingface.co/docs/smolagents/en/index"},
                {"id": "2", "title": "Introducing smolagents: A Lightweight Library for Building ...", "url": "https://medium.com/thedeephub/introducing-smolagents-a-lightweight-library-for-building-powerful-agents-a8791a60b5b1"},
            ]})}
        ],
        "tools": [tools["search_google_api"], tools["web_qa"]]
    }
]

TEMPLATE_ACTION = r"""Action:
{
  "name": "{{action_name}}",
  "arguments": {{action_arguments}}
}"""
template_action = jinja_env.from_string(TEMPLATE_ACTION)
def process_messages(messages: list[ChatCompletionMessageParam]) -> list[ChatCompletionMessageParam]:
    result = []
    for message in messages:
        if message["role"] == "tool":
            content = f"Observation: {message['content']}"
            # Constraint from openai SDK: the message before role="tool" must be role="assistant" with corresponding tool_call
            result.append({"role": "user", "content": content})
        elif message["role"] == "assistant":
            # FIXME: content? no-FC?
            if message.get("tool_calls"):
                tool_call = message["tool_calls"][0]
                tool_call_str = template_action.render(action_name=tool_call["function"]["name"], action_arguments=tool_call["function"]["arguments"])
            content = message.get("content", "")
            assert any([content, tool_call_str]), "content or tool_call cannot be empty"
            new_content = "\n".join([content, tool_call_str]) if content else tool_call_str
            result.append({"role": "assistant", "content": new_content})
        else:
            result.append(message)
    print(f">> Converted messages:\n{result}")
    return result


# from https://github.com/huggingface/smolagents/blob/main/src/smolagents/prompts/toolcalling_agent.yaml
TEMPLATE = r"""
You are an expert assistant who can solve any task using tool calls. You will be given a task to solve as best you can.
To do so, you have been given access to some tools.

The tool call you write is an action: after the tool is executed, you will get the result of the tool call as an "observation".
This Action/Observation can repeat N times, you should take several steps when needed.

Here are a few examples using notional tools:
---
Task: "Generate an image of the oldest person in this document."

Action:
{
    "name": "document_qa",
    "arguments": {"document": "document.pdf", "question": "Who is the oldest person mentioned?"}
}
Observation: "The oldest person in the document is John Doe, a 55 year old lumberjack living in Newfoundland."

Action:
{
    "name": "image_generator",
    "arguments": {"prompt": "A portrait of John Doe, a 55-year-old man living in Canada."}
}
Observation: "image.png"

Action:
{
    "name": "final_answer",
    "arguments": "image.png"
}

---
Task: "What is the result of the following operation: 5 + 3 + 1294.678?"

Action:
{
    "name": "python_interpreter",
    "arguments": {"code": "5 + 3 + 1294.678"}
}
Observation: 1302.678

Action:
{
    "name": "final_answer",
    "arguments": "1302.678"
}

Above example were using notional tools that might not exist for you. You only have access to these tools:
{%- for tool in tools %}
- {{ tool.function.name }}: {{ tool.function.description }}
    Takes inputs: {{tool.function.parameters}}
{%- endfor %}

{%- if managed_agents and managed_agents.values() | list %}
You can also give tasks to team members.
Calling a team member works the same as for calling a tool: simply, the only argument you can give in the call is 'task', a long string explaining your task.
Given that this team member is a real human, you should be very verbose in your task.
Here is a list of the team members that you can call:
{%- for agent in managed_agents.values() %}
- {{ agent.name }}: {{ agent.description }}
{%- endfor %}
{%- endif %}
""".strip()
def process(task: dict) -> dict:
    # 1. sp
    template = jinja_env.from_string(TEMPLATE)
    sp = template.render(tools=task["tools"])
    # 2. messages
    messages = process_messages(task["messages"])
    return {
        "messages": [
            {"role": "system", "content": sp},
            *messages
        ],
        "stop": ["Observation:"]
    }

async def main():
    def print_chat_completion(result: ChatCompletion):
        messages = result.choices[0].message
        content = messages.content
        tool_calls =[tc.function.model_dump() for tc in messages.tool_calls] if messages.tool_calls else []
        return {"content": content, "tool_calls": tool_calls}
        
        
    tasks = tasks_multi
    for i, task in enumerate(tasks):
        result_fc = await simplified_openai.chat_completion(**task)
        result_react = await simplified_openai.chat_completion(**process(task))
        print(f"[{i+1:02d}/{len(tasks):02d}] {task['messages'][0]['content']}")
        print(f"FC: {print_chat_completion(result_fc)}")
        print(f"React: {print_chat_completion(result_react)}")


if __name__ == "__main__":
    asyncio.run(main())
