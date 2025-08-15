import asyncio
import logging

import agents as ag
import gradio as gr


class GradioChatbot:

    def __init__(self, simple_agent, example_query=""):
        self.simple_agent = simple_agent
        self.user_interrupted = False
        self.user_interrupted_lock = asyncio.Lock()
        self.example_query = example_query

        with gr.Blocks(theme=gr.themes.Soft()) as demo:
            gr.Markdown("# uTu Agent Gradio Demo")
            with gr.Row():
                with gr.Column(scale=1):
                    chatbot = gr.Chatbot(label="Chatbot", type="messages")
                    user_input = gr.Textbox(
                        label="Your Input",
                        placeholder="Type your message here...",
                        value=self.example_query,
                    )
                    with gr.Row():
                        with gr.Column():
                            submit_button = gr.Button("Submit")
                        with gr.Column():
                            cancel_button = gr.Button("Cancel")

            gr.Markdown("This is a simple agent demo using uTu framework.")

            async def check_and_reset_user_interrupt():
                async with self.user_interrupted_lock:
                    if self.user_interrupted:
                        self.user_interrupted = False
                        return True
                return False

            async def set_user_interrupt(user_interrupted_: bool = True):
                async with self.user_interrupted_lock:
                    self.user_interrupted = user_interrupted_

            async def respond(message, history):
                if message.strip() == "":
                    return
                global built

                await set_user_interrupt(False)

                chat_message = {"role": "user", "content": message}
                self.simple_agent.input_items.append(chat_message)
                history.append(chat_message)
                yield history

                stream = self.simple_agent.run_streamed(self.simple_agent.input_items)
                async for event in stream.stream_events():
                    logging.info(f"Event: {event}")
                    if await check_and_reset_user_interrupt():
                        stream.cancel()
                        history.append(
                            {
                                "role": "assistant",
                                "content": "User interrupted the response.",
                                "metadata": {"title": "🛑 interrupted"},
                            }
                        )
                        yield history
                        break
                    if isinstance(event, ag.RawResponsesStreamEvent):
                        if event.data.type == "response.output_text.delta":
                            if (
                                history
                                and history[-1]["role"] == "assistant"
                                and "metadata" not in history[-1]
                            ):
                                history[-1]["content"] += event.data.delta
                            else:
                                history.append(
                                    {"role": "assistant", "content": event.data.delta}
                                )
                        elif event.data.type == "response.reasoning_summary_text.delta":
                            if (
                                history
                                and history[-1]["role"] == "assistant"
                                and ("metadata" in history[-1])
                                and history[-1]["metadata"]["type"] == "reasoning"
                            ):
                                history[-1]["content"] += event.data.delta
                            else:
                                history.append(
                                    {
                                        "role": "assistant",
                                        "content": f"[Reasoning]: {event.data.delta}",
                                        "metadata": {
                                            "title": "🤔 reasoning",
                                            "type": "reasoning",
                                        },
                                    }
                                )
                        elif event.data.type == "response.reasoning_summary_text.done":
                            if (
                                history
                                and history[-1]["role"] == "assistant"
                                and ("metadata" in history[-1])
                                and history[-1]["metadata"]["type"] == "reasoning"
                            ):
                                history[-1][
                                    "content"
                                ] += "... [Reasoning Completed] ..."
                        elif event.data.type == "response.output_item.added":
                            item = event.data.item
                            if item.type == "function_call":
                                history.append(
                                    {
                                        "role": "assistant",
                                        "content": "",
                                        "metadata": {
                                            "title": f"🛠️ tool_call {item.name}",
                                            "type": "tool_call",
                                        },
                                    }
                                )
                            elif item.type == "reasoning":
                                history.append(
                                    {
                                        "role": "assistant",
                                        "content": "",
                                        "metadata": {
                                            "title": "🤔 reasoning",
                                            "type": "reasoning",
                                        },
                                    }
                                )
                        elif (
                            event.data.type == "response.function_call_arguments.delta"
                        ):
                            if (
                                history
                                and history[-1]["role"] == "assistant"
                                and ("metadata" in history[-1])
                                and history[-1]["metadata"]["type"] == "tool_call"
                            ):
                                history[-1]["content"] += event.data.delta
                            else:
                                history.append(
                                    {
                                        "role": "assistant",
                                        "content": event.data.delta,
                                        "metadata": {
                                            "title": "🛠️ tool_call",
                                            "type": "tool_call",
                                        },
                                    }
                                )
                        elif event.data.type == "response.function_call_arguments.done":
                            if (
                                history
                                and history[-1]["role"] == "assistant"
                                and ("metadata" in history[-1])
                                and history[-1]["metadata"]["type"] == "tool_call"
                            ):
                                history[-1][
                                    "content"
                                ] += "... [Tool Call Arguments Completed] ..."
                        elif event.data.type in ("response.output_text.done",):
                            pass
                        elif event.data.type in (
                            "response.created",
                            "response.completed",
                            "response.in_progress",
                            "response.content_part.added",
                            "response.content_part.done",
                            "response.output_item.added",
                            "response.output_item.done",
                            "response.function_call_arguments.delta",
                            "response.function_call_arguments.done",
                        ):
                            pass
                    elif isinstance(event, ag.RunItemStreamEvent):
                        print(f"-------- {event.item.type} --------")
                        item = event.item
                        if item.type == "message_output_item":
                            pass
                        elif item.type == "tool_call_item":
                            pass
                        elif item.type == "tool_call_output_item":
                            history.append(
                                {
                                    "role": "assistant",
                                    "content": f"{item.output}",
                                    "metadata": {"title": "tool_output"},
                                }
                            )
                        else:
                            pass
                    elif isinstance(event, ag.AgentUpdatedStreamEvent):
                        new_agent = event.new_agent.name
                        history.append(
                            {
                                "role": "assistant",
                                "content": f"new agent: {new_agent}",
                                "metadata": {"title": "new agent"},
                            }
                        )
                    else:
                        pass
                    yield history

                self.simple_agent.input_items = stream.to_input_list()
                self.simple_agent.current_agent = stream.last_agent

            async def cancel_response():
                await set_user_interrupt(True)

            submit_button.click(
                respond, inputs=[user_input, chatbot], outputs=[chatbot]
            )
            cancel_button.click(cancel_response, inputs=[], outputs=[])
            user_input.submit(respond, inputs=[user_input, chatbot], outputs=[chatbot])

        self.ui = demo

    def launch(self):
        self.ui.launch(share=False)
