## Setup
Setup Youtu-Agent following instructions in [GitHub](https://github.com/TencentCloudADP/youtu-agent)

The only environment variables needed here are LLM settings:

```sh
UTU_LLM_TYPE=chat.completions
UTU_LLM_MODEL=
UTU_LLM_BASE_URL=
UTU_LLM_API_KEY=
```


## Case 1: QA with Python tool

- config: `configs/agents/examples/rl_train/qa_python.yaml`
- tools: Python executor. Here we choose the built-in [Python tool](../../utu/tools/python_executor_toolkit.py) (which runs in a subprocess). You can also use remote code sandbox like [SandboxFusion](https://bytedance.github.io/SandboxFusion/).

```sh
python scripts/cli_chat.py --config examples/rl_train/qa_python
```


## Case 2: multi-hop QA with retrieval tool (wiki)

- config: `configs/agents/examples/rl_train/qa_wiki.yaml`
- retrieval API: serving the `Wikipedia 2018` dataset. You can use this [script](https://github.com/inclusionAI/ASearcher/blob/main/scripts/launch_local_server.sh) from ASearcher to launch a local wikipedia retrieval service. 
- tools: [wiki_tool.py](./wiki_tool.py). Note to set the correct retrieval API URL in the code.

```sh
python scripts/cli_chat.py --config examples/rl_train/qa_wiki
```
