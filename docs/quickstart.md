# Quickstart

This guide will walk you through setting up the project, running your first agent, and executing evaluations.

## 1. Installation & Setup

First, clone the repository and set up the Python environment.

```sh
# Clone the project repository
git clone https://github.com/Tencent/uTu-agent.git
cd uTu-agent

# We use `uv` to manage the virtual environment and dependencies
# Create the virtual environment
uv venv

# Activate the environment
source .venv/bin/activate

# Install all dependencies, including development tools
uv sync --group dev

# Create your environment configuration file from the example
cp .env.example .env
```

After creating the `.env` file, you **must** edit it to add your necessary API keys (e.g., `OPENAI_API_KEY`, `SERPER_API_KEY`, etc.).

---

## 2. Running an Agent

You can interact with agents directly from the command line using the `cli_chat.py` script.

### Simple Agent

Run a simple agent defined by a configuration file. For example, to run an agent with search capabilities:

```sh
# python scripts/cli_chat.py --help
python scripts/cli_chat.py --config_name simple_agents/search_agent.yaml --stream
```

### Orchestra Agent

Run a multi-agent (Plan-and-Execute) orchestra agent by specifying its configuration file:

```sh
# TODO: add a web UI for orchestra agent
```

---

## 3. Running Evaluations

The framework includes a powerful evaluation harness to benchmark agent performance.

### Run a Full Experiment

This command runs a complete evaluation, from agent rollout to judging.

```sh
python scripts/run_eval.py --config_name <your_eval_config> --exp_id <your_exp_id> --dataset WebWalkerQA --concurrency 5
```

### Re-judge Existing Results

If you have already run the rollout and only want to re-run the judgment phase, use this script:

```sh
python scripts/run_eval_judge.py --config_name <your_eval_config> --exp_id <your_exp_id> --dataset WebWalkerQA
```

### Dump Experiment Data

You can also dump the trajectories and results from the database for a specific experiment:

```sh
python scripts/db/dump_db.py --exp_id "<your_exp_id>"
```

---

## 4. Advanced Setup

### Database Configuration

The evaluation framework uses a SQL database (defaulting to SQLite) to store datasets and experiment results. To use a different database (e.g., PostgreSQL), set the `DB_URL` environment variable:

```sh
export DB_URL="postgresql://user:password@host:port/database"
```

### Tracing

We use [Phoenix](https://arize.com/docs/phoenix) as our default tracing service for observing agent behavior. To enable it, set the following environment variables:
- `PHOENIX_ENDPOINT`
- `PHOENIX_BASE_URL`
- `PHOENIX_PROJECT_NAME`

The framework also supports any tracing service compatible with the `openai-agents` library. See the [official list of tracing processors](https://openai.github.io/openai-agents-python/tracing/#external-tracing-processors-list) for more options.

---

## 5. Next Steps

- **Explore Examples**: Check the `/examples` directory for more detailed use cases and advanced scripts.
- **Dive into Evaluations**: Learn more about how the evaluation framework works by reading the [Evaluation Framework documentation](./eval.md).
