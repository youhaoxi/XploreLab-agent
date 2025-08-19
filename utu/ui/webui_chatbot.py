import asyncio
import json
from dataclasses import asdict, dataclass
from importlib import resources
from typing import Literal

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
class Event:
    type: Literal["raw", "orchestra", "finish", "example"]
    data: TextDeltaContent | OrchestraContent | ExampleContent | None = None


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
                        stream = self.agent.run_streamed(self.agent.input_items)
                    else:
                        raise ValueError(f"Unsupported agent type: {type(self.agent).__name__}")

                    async for event in stream.stream_events():
                        event_to_send = None
                        if isinstance(event, ag.RawResponsesStreamEvent):
                            if event.data.type == "response.output_text.delta":
                                if event.data.delta != "":
                                    event_to_send = Event(
                                        type="raw",
                                        data=TextDeltaContent(
                                            type="text",
                                            delta=event.data.delta,
                                            inprogress=True,
                                        ),
                                    )
                            elif event.data.type == "response.output_text.done":
                                event_to_send = Event(
                                    type="raw",
                                    data=TextDeltaContent(
                                        type="text",
                                        delta=event.data.delta,
                                        inprogress=False,
                                    ),
                                )
                            elif event.data.type == "response.reasoning_summary_text.delta":
                                if event.data.delta != "":
                                    event_to_send = Event(
                                        type="raw",
                                        data=TextDeltaContent(
                                            type="reason",
                                            delta=event.data.delta,
                                            inprogress=True,
                                        ),
                                    )
                            elif event.data.type == "response.reasoning_summary_text.done":
                                event_to_send = Event(
                                    type="raw",
                                    data=TextDeltaContent(
                                        type="reason",
                                        delta=event.data.delta,
                                        inprogress=False,
                                    ),
                                )
                            elif event.data.type == "response.function_call_arguments.delta":
                                # if event.data.delta != '':
                                #     event_to_send = Event(type="raw", data=TextDeltaContent(
                                #         type="tool_call_argument",
                                #         delta=event.data.delta,
                                #         inprogress=True,
                                #     ))
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
                                    event_to_send = Event(
                                        type="raw",
                                        data=TextDeltaContent(
                                            type="reason",
                                            delta=item.summary,
                                            inprogress=False,
                                        ),
                                    )
                                elif item.type == "message":
                                    pass
                            elif event.data.type == "response.function_call_arguments.done":
                                # event_to_send = Event(type="raw", data=TextDeltaContent(
                                #     type="tool_call_argument",
                                #     delta=event.data.delta,
                                #     inprogress=False,
                                # ))
                                pass
                            elif event.data.type == "response.output_item.added":
                                item = event.data.item
                                if item.type == "function_call":
                                    # event_to_send = Event(type="raw", data=TextDeltaContent(
                                    #     type="tool_call",
                                    #     delta=item.name,
                                    #     inprogress=True,
                                    #     tool_name=item.name,
                                    # ))
                                    pass
                                elif item.type == "reasoning":
                                    event_to_send = Event(
                                        type="raw",
                                        data=TextDeltaContent(
                                            type="reason",
                                            delta="",
                                            inprogress=True,
                                        ),
                                    )
                                elif item.type == "message":
                                    event_to_send = Event(
                                        type="raw",
                                        data=TextDeltaContent(
                                            type="text",
                                            delta="",
                                            inprogress=True,
                                        ),
                                    )
                            else:
                                event_to_send = None
                        elif isinstance(event, ag.RunItemStreamEvent):
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
                            else:
                                pass
                        elif isinstance(event, ag.AgentUpdatedStreamEvent):
                            pass
                        elif isinstance(event, OrchestraStreamEvent):
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
                        else:
                            pass
                        if event_to_send:
                            # print(f"Sending event: {asdict(event_to_send)}")
                            self.write_message(asdict(event_to_send))
                    else:
                        event_to_send = Event(type="finish")
                        self.write_message(asdict(event_to_send))
                        if isinstance(self.agent, SimpleAgent):
                            self.agent.input_items = stream.to_input_list()
                            self.agent.current_agent = stream.last_agent
                except TypeError:
                    # print(f"Invalid query format: {e}")
                    self.close(1002, "Invalid query format")
            else:
                # print(f"Unhandled message type: {data.get('type')}")
                self.close(1002, "Unhandled message type")
        except json.JSONDecodeError:
            # print(f"Invalid JSON received: {message}")
            self.close(1002, "Invalid JSON received")
        except Exception:
            # print(f"Error processing message: {str(e)}")
            # stack trace
            # import traceback
            # print(traceback.format_exc())
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

    def launch(self, port: int = 8848):
        asyncio.run(self.__launch(port=port))


if __name__ == "__main__":
    webui = WebUIChatbot()
    webui.launch()
