# Quickstart

## Run example

```sh
# 1. mcp
python examples/mcp/main.py
# 2. eval
python examples/eval/main.py
```


## Run exp

```sh
# ... setup env
python scripts/run_eval.py --config_name v01 --exp_id "v0.1_dsv3"

# dump output (set --clear_records if you want to clear records)
python scripts/dump_db.py --exp_id "v0.1_dsv3"

# analysis
python scripts/analysis/tool_usage.py --exp_id "v0.1_dsv3"
```

