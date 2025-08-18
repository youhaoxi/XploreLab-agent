# Youtu-agent: A simple yet powerful agents framework from Tencent Youtu Lab.

<div align="center">
<a href="./docs/index.md"><img src=https://img.shields.io/badge/📖-Documentation-blue.svg></a>
<a href=https://arxiv.org/abs/2502.14345><img src=https://img.shields.io/badge/arXiv-2502.14345-b31b1b.svg></a>
<a href=https://github.com/Tencent/uTu-agent><img src=https://img.shields.io/badge/GitHub-Tencent-blue.svg></a>
</div>

`Youtu-agent` is a flexible, high-performance framework for building, running, and evaluating autonomous agents. Designed with modularity and extensibility in mind, it provides a strong baseline for researchers and a reliable scaffolding for developers, achieving state-of-the-art results on complex reasoning and interaction benchmarks.


## 🚀 Performance Highlights

Leveraging open-source models, `Youtu-agent` has achieved state-of-the-art (SOTA) performance on challenging deep search and reasoning benchmarks.

- **[GAIA](https://gaia-benchmark-leaderboard.hf.space/)**: Achieved **70.90%** accuracy, demonstrating strong general problem-solving capabilities with a fully open-source model stack.
- **[WebWalkerQA](https://huggingface.co/datasets/callanwu/WebWalkerQA)**: Achieved **60.71%** accuracy using `DeepSeek-V3-0324`, significantly outperforming previous SOTA models.


## ✨ Features

### 1. Simple yet Powerful Baseline
- **Proven Performance**: Our straightforward framework is proven effective on benchmarks, providing a strong starting point for model training and experimental comparisons.
- **Extensible Architecture**: Easily create and plug in new tools, models, and environments to suit your needs.

### 2. Modular and Validated Architecture
- **Environment Encapsulation**: A dedicated `Environment` module allows for custom agent operating environments, supporting persistent state and dynamic tool management.
- **Customizable Context Management**: The `ContextManager` module enables advanced features like long-context control and dynamic state injection.
- **Effective Agent Paradigms**: We provide two battle-tested agent paradigms: `SimpleAgent` (ReAct-style) and `OrchestraAgent` (Plan-and-Execute).

### 3. Flexible and Efficient by Design
- **Broad Model Compatibility**: Built on `openai-agents`, it natively supports both `chat.completions` and `responses` APIs.
- **Asynchronous**: Designed with `asyncio` for high-performance, concurrent operations.
- **Comprehensive Tracing**: In addition to OTEL, we provide a `DBTracingProcessor` system designed for in-depth analysis of tool calls and agent trajectories.

### 4. Automatation
- **Automated Agent Configuration**: Generate agent configurations automatically from structured requirements.
- **Tool Optimization**: Since tool quality is critical, the framework includes capabilities for tool evaluation and automated optimization.

## 🤔 Why Youtu-agent?

`Youtu-agent` is designed to provide significant value to different user groups:

- **For Agents Researchers & LLM Trainers**:
    - A **simple yet powerful baseline** that is stronger than basic ReAct, serving as an excellent starting point for model training and ablation studies.
    - **Built-in support for common benchmarks** and one-click evaluation scripts to streamline the experimental process.
- **For Agent Application Developers**:
    - A **proven and portable scaffolding** for building real-world agent applications.
    - **Ease of Use**: Get started quickly with simple scripts and a rich set of built-in toolkits.
    - **Modular Design**: Key components like `Environment` and `ContextManager` are encapsulated yet highly customizable.
- **For AI & Agent Enthusiasts**:
    - **Practical Use Cases**: The `/examples` directory includes tasks like deep research report generation, data analysis, and personal file organization.
    - **Simplicity & Debuggability**: A rich toolset and visual tracing tools make development and debugging intuitive and straightforward.


## 🧩 Core Concepts

- **Agent**: An LLM configured with specific prompts, tools, and an environment.
- **Toolkit**: An encapsulated set of tools that an agent can use.
- **Environment**: The world in which the agent operates (e.g., a browser, a shell).
- **ContextManager**: A configurable module for managing the agent's context window.
- **Benchmark**: An encapsulated workflow for a specific dataset, including preprocessing, rollout, and judging logic.

## 🚀 Getting Started

First, ensure you have completed the initial setup (clone repo, install dependencies).

### Quickstart

This example runs a simple agent equipped with a web search tool.

**1. Create a config file:**
```yaml
# configs/agents/sample_tool.yaml
defaults:
  - /model/base
  - /tools/search@toolkits.search # Loads the 'search' toolkit
  - _self_

agent:
    name: simple-tool-agent
    instructions: "You are a helpful assistant that can search the web."
```

**2. Write and run the Python script:**
```python
import asyncio
from utu.agents import SimpleAgent

async def main():
    async with SimpleAgent(config="sample_tool.yaml") as agent:
        await agent.chat("What's the weather in Beijing today?")

asyncio.run(main())
```

See [quickstart](./docs/quickstart.md) for more details.


### Using Examples

You can try running the examples, such as a deep research agent.
```bash
python -m examples.research.main
```

See [examples](./docs/examples.md) for more examples.

### Evaluation

Run the full evaluation pipeline on a benchmark like WebWalkerQA.
```bash
python scripts/run_eval.py --config_name ww --exp_id <your_exp_id> --dataset WebWalkerQA --concurrency 5
```

See [evaluation](./docs/evaluation.md) for more details.


## Acknowledgements

This project builds upon the excellent work of several open-source projects:
- [openai-agents](https://github.com/openai/openai-agents-python/)
- [mkdocs-material](https://github.com/squidfunk/mkdocs-material)
- [model-context-protocol](https://github.com/modelcontextprotocol/python-sdk)

## Citation

If you find this work useful, please consider citing our paper:

```bibtex
@misc{youtu-agent-2025,
  title={Youtu-agent: A Simple yet Powerful Agent Framework},
  author={Tencent Youtu Lab},
  year={2025},
  eprint={2502.14345},
  archivePrefix={arXiv},
  primaryClass={cs.AI}
}
```
