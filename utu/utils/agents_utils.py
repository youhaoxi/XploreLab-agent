import os
import json
import uuid
import logging
from typing import Literal
from collections.abc import AsyncIterator, Iterable

from openai import AsyncOpenAI
from openai.types.responses import ResponseFunctionToolCall, FunctionToolParam
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam

from agents import (
    HandoffOutputItem, TResponseInputItem, 
    ItemHelpers,
    MessageOutputItem,
    OpenAIChatCompletionsModel, OpenAIResponsesModel,
    RunItem, ModelSettings, ModelTracing,
    StreamEvent,
    RunResult,
    ToolCallItem, FunctionTool,
    ToolCallOutputItem,
)
from agents.stream_events import AgentUpdatedStreamEvent, RawResponsesStreamEvent, RunItemStreamEvent
from agents.models.chatcmpl_converter import Converter

from .print_utils import PrintUtils
from .openai_utils import OpenAIChatCompletionParams, OpenAIUtils

logger = logging.getLogger(__name__)



class ChatCompletionConverter(Converter):
    @classmethod
    def items_to_messages(cls, items: str|Iterable[TResponseInputItem]) -> list[ChatCompletionMessageParam]:
        # skip reasoning, see chatcmpl_converter.Converter.items_to_messages()
        # agents.exceptions.UserError: Unhandled item type or structure: {'id': '__fake_id__', 'summary': [{'text': '...', 'type': 'summary_text'}], 'type': 'reasoning'}
        if not isinstance(items, str):  # TODO: check it!
            items = cls.filter_items(items)
        return Converter.items_to_messages(items)

    @classmethod
    def filter_items(cls, items: str|Iterable[TResponseInputItem]) -> str|list[TResponseInputItem]:
        if isinstance(items, str):
            return items
        filtered_items = []
        for item in items:
            if item.get("type", None) == "reasoning":
                continue
            filtered_items.append(item)
        return filtered_items



    @classmethod
    def items_to_dict(cls, items: str|Iterable[TResponseInputItem]) -> list[dict]:
        """convert items to a list of dict which have {"role", "content"}"""
        if isinstance(items, str):
            return [{"role": "user", "content": items}]
        result = []
        for item in items:
            if msg := Converter.maybe_easy_input_message(item): result.append(msg)
            elif msg := Converter.maybe_input_message(item): result.append(msg)
            elif msg := Converter.maybe_response_output_message(item): result.append(msg)
            elif msg := Converter.maybe_file_search_call(item):
                msg.update({"role": "tool", "content": msg["results"]})
                result.append(msg)
            elif msg := Converter.maybe_function_tool_call(item):
                msg.update({"role": "assistant", "content": f"{msg['name']}({msg['arguments']})"})
                result.append(msg)
            elif msg := Converter.maybe_function_tool_call_output(item):
                msg.update({"role": "tool", "content": msg["output"], "tool_call_id": msg["call_id"]})
                result.append(msg)
            elif msg := Converter.maybe_reasoning_message(item):
                msg.update({"role": "assistant", "content": msg["summary"]})
                result.append(msg)
            else:
                logger.warning(f"Unknown message type: {item}")
                result.append({"role": "assistant", "content": f"Unknown message type: {item}"})
        return result


class AgentsUtils:
    @staticmethod
    def generate_group_id() -> str:
        """Generate a unique group ID. (Used in OpenAI tracing)
        Ref: https://openai.github.io/openai-agents-python/tracing/
        """
        return uuid.uuid4().hex[:16]

    @staticmethod
    def get_agents_model(
        type: Literal["responses", "chat.completions"] = None,
        model: str = None,
        base_url: str = None,
        api_key: str = None,
    ) -> OpenAIChatCompletionsModel | OpenAIResponsesModel:
        type = type or os.getenv("UTU_LLM_TYPE", "chat.completions")
        model = model or os.getenv("UTU_LLM_MODEL")
        base_url = base_url or os.getenv("UTU_LLM_BASE_URL")
        api_key = api_key or os.getenv("UTU_LLM_API_KEY")
        if not api_key or not base_url:
            raise ValueError("UTU_LLM_API_KEY and UTU_LLM_BASE_URL must be set")
        openai_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        if type == "chat.completions":
            return OpenAIChatCompletionsModel(model=model, openai_client=openai_client)
        elif type == "responses":
            return OpenAIResponsesModel(model=model, openai_client=openai_client)
        else:
            raise ValueError("Invalid type: " + type)

    @staticmethod
    def get_trajectory_from_agent_result(agent_result: RunResult) -> dict:
        return {
            "agent": agent_result.last_agent.name,
            "trajectory": ChatCompletionConverter.items_to_dict(agent_result.to_input_list()),
        }

    @staticmethod
    def print_new_items(new_items: list[RunItem]) -> None:
        """Print new items generated by Runner.run()"""
        for new_item in new_items:
            agent_name = new_item.agent.name
            if isinstance(new_item, MessageOutputItem):
                PrintUtils.print_bot(f"{agent_name}: {ItemHelpers.text_message_output(new_item)}")
            elif isinstance(new_item, HandoffOutputItem):
                PrintUtils.print_info(f"Handed off from {new_item.source_agent.name} to {new_item.target_agent.name}")
            elif isinstance(new_item, ToolCallItem):
                assert isinstance(new_item.raw_item, ResponseFunctionToolCall)  # DONOT use openai's built-in tools
                PrintUtils.print_info(
                    f"{agent_name}: Calling a tool: {new_item.raw_item.name}({json.loads(new_item.raw_item.arguments)})"  # node that API always return the json string
                )
            elif isinstance(new_item, ToolCallOutputItem):
                PrintUtils.print_tool(f"Tool call output: {new_item.output}")
            else:
                PrintUtils.print_info(f"{agent_name}: Skipping item: {new_item.__class__.__name__}")

    @staticmethod
    async def print_stream_events(result: AsyncIterator[StreamEvent]) -> None:
        """Print stream events generated by Runner.run_streamed()"""
        async for event in result:
            if isinstance(event, RawResponsesStreamEvent):
                # event.data -- ResponseStreamEvent
                if event.data.type == "response.output_text.delta":
                    PrintUtils.print_info(f"{event.data.delta}", end="")
                elif event.data.type in ("response.output_text.done",):
                    PrintUtils.print_info("")
                elif event.data.type in (
                    "response.created", "response.completed", "response.in_progress",
                    "response.content_part.added", "response.content_part.done"
                    "response.output_item.added", "response.output_item.done",
                    "response.function_call_arguments.delta", "response.function_call_arguments.done",
                ):
                    pass
            elif isinstance(event, RunItemStreamEvent):
                item: RunItem = event.item
                if item.type == "message_output_item":
                    PrintUtils.print_bot(f"<{item.agent.name}> {ItemHelpers.text_message_output(item).strip()}")
                # elif item.type == "handoff_call_item":  # same as `ToolCallItem`
                #     PrintUtils.print_bot(f"<{item.agent.name}> [handoff_call] {item.raw_item.name}({item.raw_item.arguments})")
                # elif item.type == "handoff_output_item":
                #     PrintUtils.print_info(f">> Handoff from {item.source_agent.name} to {item.target_agent.name}")
                elif item.type == "tool_call_item":
                    PrintUtils.print_bot(f"<{item.agent.name}> [tool_call] {item.raw_item.name}({item.raw_item.arguments})")
                elif item.type == "tool_call_output_item":
                    PrintUtils.print_tool(f"<{item.agent.name}> [tool_output] {item.output}")  # item.raw_item
                else:
                    assert event.type in ("reasoning_item", "mcp_list_tools_item", "mcp_approval_request_item", "mcp_approval_response_item")
                    PrintUtils.print_info(f"  >>> Skipping item: {item.__class__.__name__}")
            elif isinstance(event, AgentUpdatedStreamEvent):
                PrintUtils.print_info(f">> new agent: {event.new_agent.name}")
        print()  # Newline after stream?

    @staticmethod
    def convert_model_settings(params: OpenAIChatCompletionParams) -> ModelSettings:
        # "tools", "messages", "model"
        # FIXME: move to extra_args
        for p in ("max_completion_tokens", "top_logprobs", "logprobs", "seed", "stop"):
            if p in params:
                logger.warning(f"Parameter `{p}` is not supported in ModelSettings")
        return ModelSettings(
            max_tokens=params.get("max_tokens", None),
            temperature=params.get("temperature", None),
            top_p=params.get("top_p", None),
            frequency_penalty=params.get("frequency_penalty", None),
            presence_penalty=params.get("presence_penalty", None),
            tool_choice=params.get("tool_choice", None),
            parallel_tool_calls=params.get("parallel_tool_calls", None),
            extra_query=params.get("extra_query", None),
            extra_body=params.get("extra_body", None),
            extra_headers=params.get("extra_headers", None),
        )

    @staticmethod
    def convert_sp_input(messages: list[ChatCompletionMessageParam]) -> tuple[str|None, str|list[TResponseInputItem]]:
        if isinstance(messages, str):
            return None, messages
        if messages[0].get("role", None) == "system":
            return messages[0]["content"], messages[1:]
        return None, messages

    @staticmethod
    def convert_tool(tool: ChatCompletionToolParam) -> FunctionTool:
        assert tool["type"] == "function"
        return FunctionTool(
            name=tool["function"]["name"],
            description=tool["function"].get("description", ""),
            params_json_schema=tool["function"].get("parameters", None),
            on_invoke_tool=None,
        )


class SimplifiedOpenAIChatCompletionsModel(OpenAIChatCompletionsModel):
    """ extend OpenAIChatCompletionsModel to support basic api 
    - enable tracing based on SimplifiedAsyncOpenAI
    """
    async def query_one(self, **kwargs) -> str:
        system_instructions, input = AgentsUtils.convert_sp_input(kwargs["messages"])
        model_settings = AgentsUtils.convert_model_settings(kwargs)
        tools = [AgentsUtils.convert_tool(tool) for tool in kwargs.get("tools", [])]
        response = await self.get_response(
            system_instructions=system_instructions,
            input=input,
            model_settings=model_settings,
            tools=tools,
            output_schema=None, handoffs=[],
            tracing=ModelTracing.ENABLED,
            previous_response_id=None, prompt=None,
        )
        return ChatCompletionConverter.items_to_messages(response.to_input_items())
        # with generation_span(
        #     model=kwargs["model"],
        #     model_config=_model_settings,
        #     input=_messages,
        # ) as span_generation:
        #     result = await self.chat.completions.create(**kwargs)
        #     span_generation.span_data.output = result.choices[0].message.model_dump()
        #     return result