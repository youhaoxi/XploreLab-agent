

```sh
# setup env
uv venv && uv sync --group dev
source .venv/bin/activate

# config
cp .env.example .env
# ... setup env

# run example
# 1. mcp
python examples/mcp/main.py
# 2. eval
python examples/eval/main.py
# 3. tool maker
python examples/tool_maker/main.py
```

# TODO
> see full in [qqdoc](https://doc.weixin.qq.com/smartsheet/s3_AcMATAZtAPIuFWU7og0T16lnjNLwZ?scode=AJEAIQdfAAojkV21HAAcMATAZtAPI&tab=q979lj&viewId=vukaF8)

- features
    - [x] basic wrapper of @openai-agents @2025-06-20
    - [x] eval workflow (rollout) @2025-06-23
    - [x] logging/tracing system @phoenix @2025-06-24
    - [x] #tool cache (reduce the cost of Google API)
    - [x] non-fc model support (ReAct mode) @2025-06-27
- agents | baseline
    - [x] #single-agent tools (search)
    - [ ] #single-agent tools + (search_tool)
    - [ ] #agent-pattern routing
- eval
    - [ ] #dataset GIAI
    - [ ] #dataset BrowseCamp
- tools
    - [x] search (google_api)
    - [x] web_qa @2025-06-26
    - [ ] integration the workflow of tool-maker (MCP) @yigeng

