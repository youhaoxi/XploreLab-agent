from typing import Iterable, Literal, Optional, TypedDict, Union

import httpx
from openai._types import NOT_GIVEN, Body, Headers, NotGiven, Query
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
from openai.types.chat.completion_create_params import ResponseFormat
from openai.types.responses import ResponseInputParam, ResponseTextConfigParam, ToolParam
from openai.types.responses.response_create_params import ToolChoice
from openai.types.shared import ChatModel, Reasoning, ReasoningEffort, ResponsesModel


class OpenAICreateBaseParams(TypedDict):
    stream: Optional[bool] = False
    # from openai.resources.chat.completions.Completions.create
    extra_headers: Headers | None = (None,)
    extra_query: Query | None = (None,)
    extra_body: Body | None = (None,)
    timeout: float | httpx.Timeout | None | NotGiven = (NOT_GIVEN,)


# CompletionCreateParams | https://platform.openai.com/docs/api-reference/chat/create
class OpenAIChatCompletionParams(TypedDict, OpenAICreateBaseParams):
    # NOTE: only for typing
    messages: Iterable[ChatCompletionMessageParam]  # required
    model: Union[str, ChatModel]  # required
    frequency_penalty: Optional[float]
    logit_bias: Optional[dict[str, int]]
    logprobs: Optional[bool]
    max_completion_tokens: Optional[int]
    max_tokens: Optional[int]
    n: Optional[int]
    presence_penalty: Optional[float]
    reasoning_effort: Optional[ReasoningEffort]
    response_format: ResponseFormat
    seed: Optional[int]
    temperature: Optional[float]
    top_p: Optional[float]
    tools: Optional[list[ChatCompletionToolParam]]
    tool_choice: Optional[Literal["none", "auto", "required"]]
    parallel_tool_calls: Optional[bool]
    stop: Optional[Union[str, list[str]]]
    top_logprobs: Optional[int]


# ResponseCreateParams | https://platform.openai.com/docs/api-reference/responses/create
class OpenAIResponsesParams(TypedDict, OpenAICreateBaseParams):
    input: Union[str, ResponseInputParam]
    instructions: Optional[str]
    max_output_tokens: Optional[int]
    max_tool_calls: Optional[int]
    model: ResponsesModel
    parallel_tool_calls: Optional[bool]
    previous_response_id: Optional[str]
    reasoning: Optional[Reasoning]
    temperature: Optional[float]
    text: ResponseTextConfigParam
    tool_choice: ToolChoice
    tools: Iterable[ToolParam]
    top_logprobs: Optional[int]
    top_p: Optional[float]
    truncation: Optional[Literal["auto", "disabled"]]


OpenAIChatCompletionParamsKeys = OpenAIChatCompletionParams.__annotations__.keys()
OpenAIResponsesParamsKeys = OpenAIResponsesParams.__annotations__.keys()
