from dataclasses import dataclass
from typing import Literal

import agents as ag

from utu.agents.orchestra import OrchestraStreamEvent


@dataclass
class TextDeltaContent:
    type: Literal["reason", "tool_call_argument", "tool_call_output", "text"]
    delta: str
    inprogress: bool = False
    callid: str | None = None
    argument: str | None = None


@dataclass
class PlanItem:
    analysis: str
    todo: list[str]


@dataclass
class WorkerItem:
    task: str
    output: str


@dataclass
class ReportItem:
    output: str


@dataclass
class OrchestraContent:
    type: Literal["plan", "worker", "report"]
    item: PlanItem | WorkerItem | ReportItem


@dataclass
class ExampleContent:
    type: Literal["example"]
    query: str


@dataclass
class NewAgentContent:
    type: Literal["new"]
    name: str


@dataclass
class Event:
    type: Literal["raw", "orchestra", "finish", "example", "new"]
    data: TextDeltaContent | OrchestraContent | ExampleContent | NewAgentContent | None = None


@dataclass
class UserQuery:
    type: Literal["query"]
    query: str


async def handle_raw_stream_events(event: ag.RawResponsesStreamEvent) -> Event | None:
    def _send_delta(
        delta: str,
        type: Literal["text", "reason", "tool_call_argument", "tool_call_output"],
        inprogress: bool = True,
        allow_empty: bool = True,
    ):
        if delta != "" or allow_empty:
            event_to_send = Event(
                type="raw",
                data=TextDeltaContent(
                    type=type,
                    delta=delta,
                    inprogress=inprogress,
                ),
            )
            return event_to_send
        return None

    event_to_send = None
    if event.data.type == "response.output_text.delta":
        event_to_send = _send_delta(event.data.delta, "text", allow_empty=False)
    elif event.data.type == "response.output_text.done":
        event_to_send = _send_delta("", "text", inprogress=False)
    elif event.data.type == "response.reasoning_text.delta":
        if isinstance(event.data.delta, list):
            event.data.delta = "".join([d["text"] for d in event.data.delta])
        event_to_send = _send_delta(event.data.delta, "reason", allow_empty=False)
    elif event.data.type == "response.reasoning_summary_text.done":
        event_to_send = _send_delta("", "reason", inprogress=False)
    elif event.data.type == "response.function_call_arguments.delta":
        pass
    elif event.data.type == "response.output_item.done":
        item = event.data.item
        if item.type == "function_call":
            event_to_send = Event(
                type="raw",
                data=TextDeltaContent(
                    type="tool_call",
                    delta=item.name,
                    argument=item.arguments,
                    callid=item.call_id,
                    inprogress=True,
                ),
            )
        elif item.type == "reasoning":
            event_to_send = _send_delta("", "reason", inprogress=False)
        elif item.type == "message":
            pass
    elif event.data.type == "response.function_call_arguments.done":
        pass
    elif event.data.type == "response.output_item.added":
        item = event.data.item
        if item.type == "function_call":
            pass
        elif item.type == "reasoning":
            event_to_send = _send_delta("", "reason", inprogress=True)
        elif item.type == "message":
            event_to_send = _send_delta("", "text", inprogress=True)
        else:
            event_to_send = None
    else:
        event_to_send = None
    return event_to_send


async def handle_orchestra_events(event: OrchestraStreamEvent) -> Event | None:
    item = event.item
    if event.name == "plan":
        todo_str = []
        for subtask in item.todo:
            task_info = f"{subtask.task} ({subtask.agent_name})"
            todo_str.append(task_info)
        plan_item = PlanItem(analysis=item.analysis, todo=todo_str)
        event_to_send = Event(type="orchestra", data=OrchestraContent(type="plan", item=plan_item))
    elif event.name == "worker":
        worker_item = WorkerItem(task=item.task, output=item.output)
        event_to_send = Event(type="orchestra", data=OrchestraContent(type="worker", item=worker_item))
    elif event.name == "report":
        report_item = ReportItem(output=item.output)
        event_to_send = Event(type="orchestra", data=OrchestraContent(type="report", item=report_item))
    else:
        pass
    return event_to_send


async def handle_tool_call_output(event: ag.RunItemStreamEvent) -> Event | None:
    item = event.item
    if item.type == "tool_call_output_item":
        event_to_send = Event(
            type="raw",
            data=TextDeltaContent(
                type="tool_call_output",
                delta=item.output,
                callid=item.raw_item["call_id"],
                inprogress=False,
            ),
        )
        return event_to_send
    return None


async def handle_new_agent(event: ag.AgentUpdatedStreamEvent) -> Event | None:
    if event.new_agent:
        if hasattr(event.new_agent, "name"):
            new_agent_name = f"{event.new_agent.name} ({event.new_agent.__class__.__name__})"
        else:
            new_agent_name = event.new_agent.__class__.__name__

        event_to_send = Event(
            type="new",
            data=NewAgentContent(type="new", name=new_agent_name),
        )
    else:
        pass
    return event_to_send
