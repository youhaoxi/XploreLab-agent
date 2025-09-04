import asyncio
import json
import logging
import os
import traceback
from importlib import resources
from pathlib import Path

import agents as ag
import tornado.web
import tornado.websocket

from utu.agents.orchestra import OrchestraStreamEvent
from utu.agents.orchestra_agent import OrchestraAgent
from utu.agents.simple_agent import SimpleAgent
from utu.config import AgentConfig
from utu.config.loader import ConfigLoader

from .common import (
    Event,
    InitContent,
    ListAgentsContent,
    SwitchAgentContent,
    SwitchAgentRequest,
    UserQuery,
    UserRequest,
    handle_new_agent,
    handle_orchestra_events,
    handle_raw_stream_events,
    handle_tool_call_output,
)

CONFIG_PATH = "configs/agents"


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def initialize(self, default_config_filename: str):
        self.default_config_filename = default_config_filename
        logging.info(f"initialize websocket, default config: {default_config_filename}")
        self.agent: SimpleAgent | OrchestraAgent | None = None
        self.default_config = None

    async def prepare(self):
        if self.default_config_filename:
            logging.info("instantiate default agent")
            self.default_config = ConfigLoader.load_agent_config(self.default_config_filename)
            await self.instantiate_agent(self.default_config)

    def check_origin(self, origin):
        # Allow all origins to connect
        return True

    def _get_config_name(self):
        return os.path.basename(self.default_config_filename)

    async def open(self):
        event_to_send = Event(type="init", data=InitContent(type="init", default_agent=self._get_config_name()))
        await self.send_event(event_to_send)

    async def send_event(self, event: Event):
        logging.debug(f"Sending event: {event.model_dump()}")
        self.write_message(event.model_dump())

    async def _handle_query(self, query: UserQuery):
        if query.query.strip() == "":
            raise ValueError("Query cannot be empty")

        if self.agent is None:
            raise RuntimeError("Agent is not initialized")

        logging.debug(f"Received query: {query.query}")

        if isinstance(self.agent, OrchestraAgent):
            stream = self.agent.run_streamed(query.query)
        elif isinstance(self.agent, SimpleAgent):
            self.agent.input_items.append({"role": "user", "content": query.query})
            stream = self.agent.run_streamed(self.agent.input_items)
        else:
            raise ValueError(f"Unsupported agent type: {type(self.agent).__name__}")

        async for event in stream.stream_events():
            logging.debug(f"Received event: {event}")
            event_to_send = None
            if isinstance(event, ag.RawResponsesStreamEvent):
                event_to_send = await handle_raw_stream_events(event)
            elif isinstance(event, ag.RunItemStreamEvent):
                event_to_send = await handle_tool_call_output(event)
            elif isinstance(event, ag.AgentUpdatedStreamEvent):
                event_to_send = await handle_new_agent(event)
            elif isinstance(event, OrchestraStreamEvent):
                event_to_send = await handle_orchestra_events(event)
            else:
                pass
            if event_to_send:
                await self.send_event(event_to_send)
        event_to_send = Event(type="finish")
        logging.debug(f"Sending event: {event_to_send.model_dump()}")
        await self.send_event(event_to_send)
        if isinstance(self.agent, SimpleAgent):
            input_list = stream.to_input_list()
            self.agent.input_items = input_list
            self.agent.current_agent = stream.last_agent

    async def _handle_list_agents(self):
        config_path = Path(CONFIG_PATH).resolve()
        config_files = config_path.glob("**/*.yaml")
        agents = [str(file.relative_to(config_path)) for file in config_files]
        await self.send_event(
            Event(
                type="list_agents",
                data=ListAgentsContent(type="list_agents", agents=agents),
            )
        )

    async def instantiate_agent(self, config: AgentConfig):
        if config.type == "simple":
            self.agent = SimpleAgent(config=config)
            await self.agent.build()
        elif config.type == "orchestra":
            self.agent = OrchestraAgent(config=config)
            await self.agent.build()
        else:
            raise ValueError(f"Unsupported agent type: {config.type}")

    async def _handle_switch_agent(self, switch_agent_request: SwitchAgentRequest):
        config = ConfigLoader.load_agent_config(switch_agent_request.config_file)
        await self.instantiate_agent(config)

    async def on_message(self, message: str):
        try:
            data = json.loads(message)
            print(data)
            request = UserRequest(**data)
            if request.type == "query":
                try:
                    await self._handle_query(request.content)
                except Exception as e:
                    logging.error(f"Error processing query: {str(e)}")
                    logging.debug(traceback.format_exc())
            elif request.type == "list_agents":
                await self._handle_list_agents()
            elif request.type == "switch_agent":
                try:
                    await self._handle_switch_agent(request.content)
                    await self.send_event(
                        Event(
                            type="switch_agent",
                            data=SwitchAgentContent(type="switch_agent", ok=True, name=request.content.config_file),
                        )
                    )
                except Exception:
                    await self.send_event(
                        Event(
                            type="switch_agent",
                            data=SwitchAgentContent(type="switch_agent", ok=False, name=request.content.config_file),
                        )
                    )
                    logging.debug(traceback.format_exc())
            else:
                logging.error(f"Unhandled message type: {data.get('type')}")
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON received: {message}")
        except Exception as e:
            logging.error(f"Error processing message: {str(e)}")
            logging.debug(traceback.format_exc())

    def on_close(self):
        logging.debug("WebSocket closed")
        pass


class WebUIAgents:
    def __init__(self, default_config: str):
        self.default_config = default_config
        # hack
        with resources.as_file(resources.files("utu_agent_ui.static").joinpath("index.html")) as static_dir:
            self.static_path = str(static_dir).replace("index.html", "")

    def make_app(self) -> tornado.web.Application:
        return tornado.web.Application(
            [
                (r"/ws", WebSocketHandler, {"default_config_filename": self.default_config}),
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

    async def __launch(self, port: int = 8848, ip: str = "127.0.0.1"):
        app = self.make_app()
        app.listen(port, address=ip)
        logging.info(f"Server started at http://{ip}:{port}/")
        await asyncio.Event().wait()

    async def launch_async(self, port: int = 8848, ip: str = "127.0.0.1"):
        await self.__launch(port=port, ip=ip)

    def launch(self, port: int = 8848, ip: str = "127.0.0.1"):
        asyncio.run(self.__launch(port=port, ip=ip))


if __name__ == "__main__":
    webui = WebUIAgents()
    webui.launch()
