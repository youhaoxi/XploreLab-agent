

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
```

