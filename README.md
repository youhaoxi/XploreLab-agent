todo | misc
- [ ] add WebWalkerQA

## Setup

```sh
# setup env
uv venv && uv sync --group dev
source .venv/bin/activate

# config
cp .env.example .env
# ... setup env
```


## Run example

```sh
# run example
# 1. mcp
python examples/mcp/main.py
# 2. eval
python examples/eval/main.py
# 3. tool maker
python examples/tool_maker/main.py
```


## Run exp

```sh
# ... setup env
# ... see config file `configs/eval/v01.yaml` for more details
python scripts/run_eval.py --config_name v01 --exp_id "v0.1_dsv3"

# dump output (set --clear_records if you want to clear records)
python scripts/dump_db.py --exp_id "v0.1_dsv3" --clear_records
```

## Run tests

```sh
# config
pytest tests/test_config.py

# tools
pytest tests/tools/test_basic_tools.py::test_run_bash
pytest tests/tools/test_search_toolkit.py::test_web_qa

# agent
pytest tests/agents/test_build_agent.py::test_build_agent

# eval
pytest tests/eval/test_eval.py
```
