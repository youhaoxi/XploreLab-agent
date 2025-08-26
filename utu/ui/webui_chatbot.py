import asyncio
import json
import traceback
import re
from dataclasses import asdict, dataclass
from importlib import resources
from typing import Literal, Optional

import agents as ag
import tornado.web
import tornado.websocket

from utu.agents.orchestra import OrchestraStreamEvent
from utu.agents.orchestra_agent import OrchestraAgent
from utu.agents.simple_agent import SimpleAgent


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


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def initialize(self, agent: SimpleAgent | OrchestraAgent, example_query: str = ""):
        self.agent: SimpleAgent | OrchestraAgent = agent
        self.example_query = example_query

    def check_origin(self, origin):
        # Allow all origins to connect
        return True

    def open(self):
        # print("WebSocket opened")
        # send example query
        self.write_message(asdict(Event("example", ExampleContent(type="example", query=self.example_query))))

    async def send_event(self, event: Event):
        # print in green color
        print(f"\033[92mSending event: {asdict(event)}\033[0m")
        self.write_message(asdict(event))
        
    async def _handle_raw_stream_events(self, event: ag.RawResponsesStreamEvent) -> Optional[Event]:
        def _send_delta(delta: str, type: Literal["text", "reason", "tool_call_argument", "tool_call_output"], inprogress: bool = True, allow_empty=True):
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
            if event.data.delta != "":
                event_to_send = _send_delta(event.data.delta, "text")
        elif event.data.type == "response.output_text.done":
            event_to_send = _send_delta("", "text", inprogress=False)
        elif event.data.type == "response.reasoning_summary_text.delta" \
            or event.data.type == "response.reasoning_text.delta":
            if event.data.delta != "":
                event_to_send = _send_delta(event.data.delta, "reason")
        elif event.data.type == "response.reasoning_summary_text.done" \
            or event.data.type == "response.reasoning_text.done":
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

    async def _handle_orchestra_events(self, event: OrchestraStreamEvent) -> Optional[Event]:
        item = event.item
        if event.name == "plan":
            todo_str = []
            for subtask in item.todo:
                task_info = f"{subtask.task} ({subtask.agent_name})"
                todo_str.append(task_info)
            plan_item = PlanItem(analysis=item.analysis, todo=todo_str)
            event_to_send = Event(
                type="orchestra", data=OrchestraContent(type="plan", item=plan_item)
            )
        elif event.name == "worker":
            worker_item = WorkerItem(task=item.task, output=item.output)
            event_to_send = Event(
                type="orchestra", data=OrchestraContent(type="worker", item=worker_item)
            )
        elif event.name == "report":
            report_item = ReportItem(output=item.output)
            event_to_send = Event(
                type="orchestra", data=OrchestraContent(type="report", item=report_item)
            )
        else:
            pass
        return event_to_send

    async def _handle_tool_call_output(self, event: ag.RunItemStreamEvent) -> Optional[Event]:
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

    async def _handle_new_agent(self, event: ag.AgentUpdatedStreamEvent) -> Optional[Event]:
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

    async def on_message(self, message: str):
        try:
            data = json.loads(message)
            if data.get("type") == "query":
                try:
                    query = UserQuery(**data)
                    # check query not empty
                    if query.query.strip() == "":
                        raise ValueError("Query cannot be empty")

                    # print(f"Received query: {query.query}")
                    # Echo back the query in the response
                    if isinstance(self.agent, OrchestraAgent):
                        stream = self.agent.run_streamed(query.query)
                    elif isinstance(self.agent, SimpleAgent):
                        self.agent.input_items.append({"role": "user", "content": query.query})
                        # print in red color
                        print(f"\033[91mInput items: {self.agent.input_items}\033[0m")
                        stream = self.agent.run_streamed(self.agent.input_items)
                    else:
                        raise ValueError(f"Unsupported agent type: {type(self.agent).__name__}")

                    async for event in stream.stream_events():
                        event_to_send = None
                        print(f"--------------------\n{event}")
                        if isinstance(event, ag.RawResponsesStreamEvent):
                            event_to_send = await self._handle_raw_stream_events(event)
                        elif isinstance(event, ag.RunItemStreamEvent):
                            event_to_send = await self._handle_tool_call_output(event)
                        elif isinstance(event, ag.AgentUpdatedStreamEvent):
                            event_to_send = await self._handle_new_agent(event)
                        elif isinstance(event, OrchestraStreamEvent):
                            event_to_send = await self._handle_orchestra_events(event)
                        else:
                            pass
                        if event_to_send:
                            # print(f"Sending event: {asdict(event_to_send)}")
                            await self.send_event(event_to_send)
                    else:
                        pass
                    event_to_send = Event(type="finish")
                    # self.write_message(asdict(event_to_send))
                    await self.send_event(event_to_send)
                    if isinstance(self.agent, SimpleAgent):
                        input_list = stream.to_input_list()
                        self.agent.input_items = input_list
                        # print in red
                        print(f"\033[91mInput list: {input_list}\033[0m")
                        self.agent.current_agent = stream.last_agent
                except TypeError as e:
                    print(f"Invalid query format: {e}")
                    # stack trace
                    print(traceback.format_exc())
                    self.close(1002, "Invalid query format")
            else:
                # print(f"Unhandled message type: {data.get('type')}")
                # self.close(1002, "Unhandled message type")
                pass
        except json.JSONDecodeError:
            # print(f"Invalid JSON received: {message}")
            self.close(1002, "Invalid JSON received")
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            # stack trace
            print(traceback.format_exc())
            self.close(1002, "Error processing message")

    def on_close(self):
        # print("WebSocket closed")
        pass


class WebUIChatbot:
    def __init__(self, agent: SimpleAgent | OrchestraAgent, example_query: str = ""):
        self.agent = agent
        self.example_query = example_query
        # hack
        with resources.as_file(resources.files("utu_agent_ui.static").joinpath("index.html")) as static_dir:
            self.static_path = str(static_dir).replace("index.html", "")

    def make_app(self) -> tornado.web.Application:
        return tornado.web.Application(
            [
                (r"/ws", WebSocketHandler, {"agent": self.agent, "example_query": self.example_query}),
                (
                    r"/",
                    tornado.web.RedirectHandler,
                    {"url": "/index.html"},
                ),
                (
                    r"/(.*)",
                    tornado.web.StaticFileHandler,
                    {"path": self.static_path, "default_filename": "index.html"},
                ),
            ],
            debug=True,
        )

    async def __launch(self, port: int = 8848):
        await self.agent.build()
        app = self.make_app()
        app.listen(port)
        print(f"Server started at http://localhost:{port}/")
        await asyncio.Event().wait()

    async def launch_async(self, port: int = 8848):
        await self.__launch(port=port)

    def launch(self, port: int = 8848):
        asyncio.run(self.__launch(port=port))


if __name__ == "__main__":
    webui = WebUIChatbot()
    webui.launch()
