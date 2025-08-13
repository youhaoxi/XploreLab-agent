import asyncio
import logging

import agents as ag
import gradio as gr

from utu.agents import SimpleAgent
from utu.config import ConfigLoader

logging.basicConfig(level=logging.INFO)


@ag.function_tool
def fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number."""
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b


config = ConfigLoader.load_agent_config("examples/base")
config.max_turns = 100
simple_agent = SimpleAgent(config=config, name="gradio-demo", tools=[fibonacci])
input_items = []
built = False
user_interrupted = False
user_interrupted_lock = asyncio.Lock()

with gr.Blocks() as demo:
    gr.Markdown("# uTu Agent Gradio Demo")
    with gr.Row():
        with gr.Column(scale=1):
            chatbot = gr.Chatbot(label="Chatbot", type="messages")
            user_input = gr.Textbox(
                label="Your Input",
                placeholder="Type your message here...",
                value="斐波那契数列的第10个数是多少？记这个数为x，数列的第x个数是多少？",
            )
            with gr.Row():
                with gr.Column(scale=0.9):
                    submit_button = gr.Button("Submit")
                with gr.Column(scale=0.1):
                    cancel_button = gr.Button("Cancel")

    info = gr.Markdown("This is a simple agent demo using uTu framework.")

    async def check_and_reset_user_interrupt():
        global user_interrupted
        async with user_interrupted_lock:
            if user_interrupted:
                user_interrupted = False
                return True
        return False

    async def set_user_interrupt(user_interrupted_: bool = True):
        global user_interrupted
        async with user_interrupted_lock:
            user_interrupted = user_interrupted_

    async def respond(message, history):
        if message.strip() == "":
            return
        global built

        await set_user_interrupt(False)

        if not built:
            await simple_agent.build()
            built = True

        chat_message = {"role": "user", "content": message}
        simple_agent.input_items.append(chat_message)
        history.append(chat_message)
        yield history

        stream = simple_agent.run_streamed(simple_agent.input_items)
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
                    if history and history[-1]["role"] == "assistant" and "metadata" not in history[-1]:
                        history[-1]["content"] += event.data.delta
                    else:
                        history.append({"role": "assistant", "content": event.data.delta})
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
                                "metadata": {"title": "🤔 reasoning", "type": "reasoning"},
                            }
                        )
                elif event.data.type == "response.reasoning_summary_text.done":
                    if (
                        history
                        and history[-1]["role"] == "assistant"
                        and ("metadata" in history[-1])
                        and history[-1]["metadata"]["type"] == "reasoning"
                    ):
                        history[-1]["content"] += "... [Reasoning Completed] ..."
                elif event.data.type == "response.output_item.added":
                    item = event.data.item
                    if item.type == "function_call":
                        history.append(
                            {
                                "role": "assistant",
                                "content": "",
                                "metadata": {"title": f"🛠️ tool_call {item.name}", "type": "tool_call"},
                            }
                        )
                    elif item.type == "reasoning":
                        history.append(
                            {
                                "role": "assistant",
                                "content": "",
                                "metadata": {"title": "🤔 reasoning", "type": "reasoning"},
                            }
                        )
                elif event.data.type == "response.function_call_arguments.delta":
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
                                "metadata": {"title": f"🛠️ tool_call", "type": "tool_call"},
                            }
                        )
                elif event.data.type == "response.function_call_arguments.done":
                    if (
                        history
                        and history[-1]["role"] == "assistant"
                        and ("metadata" in history[-1])
                        and history[-1]["metadata"]["type"] == "tool_call"
                    ):
                        history[-1]["content"] += "... [Tool Call Arguments Completed] ..."
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
                        {"role": "assistant", "content": f"{item.output}", "metadata": {"title": "tool_output"}}
                    )
                else:
                    pass
            elif isinstance(event, ag.AgentUpdatedStreamEvent):
                new_agent = event.new_agent.name
                history.append(
                    {"role": "assistant", "content": f"new agent: {new_agent}", "metadata": {"title": "new agent"}}
                )
            else:
                pass
            yield history

        simple_agent.input_items = stream.to_input_list()
        simple_agent.current_agent = stream.last_agent

    async def dummy_respond(message, history):
        """Dummy response to simulate a chat interaction. For test only"""
        fake_responses = [
            "Hello, how are you?",
            "I'm doing well, thank you.",
            "What's your name?",
            "My name is uTu.",
            "Nice to meet you.",
            "How are you doing today?",
        ]
        history.append({"role": "user", "content": message})
        for response in fake_responses:
            history.append({"role": "assistant", "content": response})
            await asyncio.sleep(1)
            yield history

    async def cancel_response():
        global user_interrupted
        await set_user_interrupt(True)

    submit_button.click(respond, inputs=[user_input, chatbot], outputs=[chatbot])
    cancel_button.click(cancel_response, inputs=[], outputs=[])
    user_input.submit(respond, inputs=[user_input, chatbot], outputs=[chatbot])

demo.launch(share=False)
