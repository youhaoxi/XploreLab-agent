import asyncio
import agents as ag
import logging
import os
import random
import argparse
import gradio as gr

from utu.agents import SimpleAgent
from utu.config import ConfigLoader
from utu.tools import BashTool

placeholder_query = "整理一下当前文件夹下面的所有文件，按照 学号-姓名 的格式重命名。我只接受学生提交的pdf，如果不是pdf文件，归档到一个文件夹里面。"

def get_tools():
    tool_config = ConfigLoader.load_toolkit_config("bash")
    logging.info(f"Loaded bash tool config: {tool_config}")
    tool_config.config["workspace_root"] = "/tmp/file_manager_test/"
    toolkit = BashTool(tool_config)
    return toolkit.get_tools_in_agents_sync()

WORKER_AGENT_PROMPT = """You are a helpful assistant. 
You are required to use `run_bash` tool to execute bash commands, help the user move, organize, and batch-rename files. 
You MUST operate strictly within the current working directory. **Never access or modify any files outside of this directory.**
Your tasks usually may include:
- Moving files to specified subdirectories.
- Renaming multiple files to a specific pattern.
- Creating or cleaning up directories as needed.
When you find the task obscure or the instructions unclear, ask for clarification before proceeding. If you encounter any issues or errors, report them immediately and wait for further instructions.

## Common Commands
The following commands are commonly used:
- `cp`: Copy files or directories.
- `mv`: Move or rename files.
- `mkdir`: Create new directories.
- `ls`: List directory contents.
- `find`: Search for files.
- `pwd`: Print the current working directory.
- `date`: Display or set the system date and time.
- `head` and `tail`: View the beginning or end of files.

## USEFUL HINTS:
1. Execute one single command at a time.
2. Inspect the results before proceeding to the next step.
3. You do not need to inform user all modifications in detail when handling files in bulk. Summarize the operations, and give some examples if necessary.

## VERY IMPORTANT RULES:
1. NEVER execute complex shell scripts with complex pattern matching, looping or piping!!
2. NEVER use `rm` command to delete files or directories. Reject any request that requires deleting files or directories. Instead, you can considering moving files to a trash directory in current workspace if the user agrees.
3. NEVER use `sudo` or any command that requires elevated privileges. Reject any request that requires elevated privileges even if the user ask you to do so.
4. NEVER access or modify files outside of the current working directory.
5. NEVER change the working directory. Never use `cd` command or any command that changes the working directory. Always use relative paths based on the current work_dir.
6. ALWAYS use relative paths based on the current working directory (aka. `.`).
7. NEVER modify the files in the current working directory unless explicitly asked to do so.
8. Avoid using commands that may produce a very large amount of output, such as `cat` on large files or `ls -lR` on directories with many files. Avoid commands that may run for a long time.
9. NEVER ask user to provide outputs of any bash command. Remember that you have access to the run_bash tool.
"""

# !TODO (lichaochen): user yaml config to load agent config
worker_agent = SimpleAgent(
    name="WorkerAgent",
    instructions=WORKER_AGENT_PROMPT,
    output_type=str,
    tools=get_tools(),
)

def prepare_messy_files():
    work_dir = "/tmp/file_manager_test"
    os.makedirs(work_dir, exist_ok=True)
    
    student_names = [
        "张三", "李四", "王五", "赵六", "孙七", "周八", "吴九", "郑十", "冯十一", "陈十二",
        "褚十三", "卫十四", "蒋十五", "沈十六", "韩十七", "杨十八", "朱十九", "秦二十", "尤二一", "许二二"
    ]
    student_numbers = [
        "2021001", "2021002", "2021003", "2021004", "2021005",
        "2021006", "2021007", "2021008", "2021009", "2021010",
        "2021011", "2021012", "2021013", "2021014", "2021015",
        "2021016", "2021017", "2021018", "2021019", "2021020",
    ]
    titles = [
        "实验报告", "课程报告", "数据结构大作业", "数据结构report", "数据结构实验报告",
        "数据结构课程报告", "数据结构实验", "数据结构大作业报告", "数据结构课程设计", "数据结构课程设计报告", "report"
    ]
    extensions = ["pdf", "docx"]
    formats = [
        "{name}{delimiter}{number}{delimiter}{title}.{extension}",
        "{number}{delimiter}{name}{delimiter}{title}.{extension}",
        "{title}{delimiter}{name}{delimiter}{number}.{extension}",
    ]
    
    for ind, student_name in enumerate(student_names):
        # create a report file for each student
        num_repeats = random.choices([1, 2, 3], weights=[0.5, 0.4, 0.1])[0]
        for i in range(num_repeats):
            file_name_format = random.choice(formats)
            file_name = file_name_format.format(
                name=student_name,
                number=student_numbers[ind],
                title=random.choice(titles),
                delimiter=random.choice(["_", "-", "", " ", "  ", "__"]),
                extension=random.choices(extensions, weights=[0.7, 0.3])[0],
            )
            file_path = os.path.join(work_dir, file_name)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"这是{student_name}的{file_name}。\n")
    print(f"Simulated messy files in {work_dir}")

async def main_cli():
    await worker_agent.build()
    print("WorkerAgent is ready to assist you with file management tasks.\n")
    
    # loop until user exit (Ctrl+D or Ctrl+C)
    try:
        while True:
            # example query:
            # "整理一下当前文件夹下面的所有文件，按照 学号-姓名.md 的格式重命名。如果不是md文件，则移动到garbage文件夹里面。"
            query = input("user> ")
            query = query.strip()
            if query == "":
                continue
            await worker_agent.chat_streamed(query)
    except (EOFError, KeyboardInterrupt):
        print("\nExiting.")

input_items = []
built = False
user_interrupted = False
user_interrupted_lock = asyncio.Lock()
simple_agent = worker_agent

with gr.Blocks() as demo:
    gr.Markdown("# uTu Agent Gradio Demo")
    with gr.Row():
        with gr.Column(scale=1):
            chatbot = gr.Chatbot(label="Chatbot", type="messages")
            user_input = gr.Textbox(label="Your Input", placeholder="Type your message here...", value=placeholder_query)
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
                history.append({"role": "assistant", "content": "User interrupted the response.", "metadata": {"title": "🛑 interrupted"}})
                yield history
                break
            if isinstance(event, ag.RawResponsesStreamEvent):
                if event.data.type == "response.output_text.delta":
                    if history and history[-1]["role"] == "assistant" and not ("metadata" in history[-1]):
                        history[-1]["content"] += event.data.delta
                    else:
                        history.append({"role": "assistant", "content": event.data.delta})
                elif event.data.type == "response.reasoning_summary_text.delta":
                    if history and history[-1]["role"] == "assistant" and ("metadata" in history[-1]) and history[-1]["metadata"]["type"] == "reasoning":
                        history[-1]["content"] += event.data.delta
                    else:
                        history.append({"role": "assistant", "content": f"[Reasoning]: {event.data.delta}", "metadata": {"title": "🤔 reasoning", "type": "reasoning"}})
                elif event.data.type == "response.reasoning_summary_text.done":
                    if history and history[-1]["role"] == "assistant" and ("metadata" in history[-1]) and history[-1]["metadata"]["type"] == "reasoning":
                        history[-1]["content"] += "... [Reasoning Completed] ..."
                elif event.data.type == "response.output_item.added":
                    item = event.data.item
                    if item.type == "function_call":
                        history.append({"role": "assistant", "content": "", "metadata": {"title": f"🛠️ tool_call {item.name}", "type": "tool_call"}})
                    elif item.type == "reasoning":
                        history.append({"role": "assistant", "content": "", "metadata": {"title": "🤔 reasoning", "type": "reasoning"}})
                elif event.data.type == "response.function_call_arguments.delta":
                    if history and history[-1]["role"] == "assistant" and ("metadata" in history[-1]) and history[-1]["metadata"]["type"] == "tool_call":
                        history[-1]["content"] += event.data.delta
                    else:
                        history.append({"role": "assistant", "content": event.data.delta, "metadata": {"title": f"🛠️ tool_call", "type": "tool_call"}})
                elif event.data.type == "response.function_call_arguments.done":
                    if history and history[-1]["role"] == "assistant" and ("metadata" in history[-1]) and history[-1]["metadata"]["type"] == "tool_call":
                        history[-1]["content"] += "... [Tool Call Arguments Completed] ..."
                elif event.data.type in ("response.output_text.done",):
                    pass
                elif event.data.type in (
                    "response.created", "response.completed", "response.in_progress",
                    "response.content_part.added", "response.content_part.done",
                    "response.output_item.added", "response.output_item.done",
                    "response.function_call_arguments.delta", "response.function_call_arguments.done",
                ):
                    pass
            elif isinstance(event, ag.RunItemStreamEvent):
                print(f'-------- {event.item.type} --------')
                item = event.item
                if item.type == "message_output_item":
                    pass
                elif item.type == "tool_call_item":
                    pass
                elif item.type == "tool_call_output_item":
                    history.append({"role": "assistant", "content": f"{item.output}", "metadata": {"title": "tool_output"}})
                else:
                    pass
            elif isinstance(event, ag.AgentUpdatedStreamEvent):
                new_agent = event.new_agent.name
                history.append({"role": "assistant", "content": f"new agent: {new_agent}", "metadata": {"title": "new agent"}})
            else:
                pass
            yield history
        
        simple_agent.input_items = stream.to_input_list()
        simple_agent.current_agent = stream.last_agent
    
    async def cancel_response():
        global user_interrupted
        await set_user_interrupt(True)
    
    submit_button.click(respond, inputs=[user_input, chatbot], outputs=[chatbot])
    cancel_button.click(cancel_response, inputs=[], outputs=[])
    user_input.submit(respond, inputs=[user_input, chatbot], outputs=[chatbot])


async def main_gradio():
    demo.launch(share=False)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    args = argparse.ArgumentParser()
    args.add_argument("--prepare", action="store_true", help="Prepare messy files in /tmp/file_manager_test")
    parsed_args = args.parse_args()

    if parsed_args.prepare:
        print("Prepare messy files...")
        prepare_messy_files()
        os.system("ls -l /tmp/file_manager_test")
        print("Messy files prepared. You can now run the agent to organize them.\n")
        exit(0)
    # asyncio.run(main())
    asyncio.run(main_gradio())