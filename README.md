# <img src="docs/assets/logo.svg" alt="Youtu-agent Logo" height="24px"> Youtu-agent: A simple yet powerful agent framework that delivers with open-source models

<div align="center">
<a href="https://tencent.github.io/Youtu-agent/"><img src=https://img.shields.io/badge/📖-Documentation-blue.svg></a>
<!-- <a href=https://arxiv.org/abs/2502.14345><img src=https://img.shields.io/badge/arXiv-2502.14345-b31b1b.svg></a> -->
<a href=https://github.com/Tencent/Youtu-agent><img src=https://img.shields.io/badge/GitHub-Tencent-blue.svg></a>
</div>

<p align="center">
| <a href="README_ZH.md"><b>中文版</b></a>
| <a href="#-benchmark-performance"><b>🌟 Performance</b></a> 
| <a href="#-examples"><b>💡 Examples</b> </a> 
| <a href="#-features"><b>✨ Features</b> </a> 
| <a href="#-getting-started"><b>🚀 Getting Started</b> </a> 
| 
</p>


`Youtu-agent` is a flexible, high-performance framework for building, running, and evaluating autonomous agents. Beyond topping the benchmarks, this framework delivers powerful agent capabilities, e.g. data analysis, file processing, and deep research, all with open-source models.

<img src="docs/assets/mascot.png" alt="Youtu-agent Logo" width="200" align="left" style="margin-right:20px;">

Key highlights:
- **Verified performance**: Achieved 71.47% on WebWalkerQA and 72.8% on GAIA (text-only subset), using purely `DeepSeek-V3` series models (without Claude or GPT), establishing a strong open-source starting point.
- **Open-source friendly & cost-aware**: Optimized for accessible, low-cost deployment without reliance on closed models.
- **Practical use cases**: Out-of-the-box support for tasks like CSV analysis, literature review, personal file organization, and podcast and video generation (coming soon).
- **Flexible architecture**: Built on [openai-agents](https://github.com/openai/openai-agents-python), with extensible support for diverse model APIs (form `DeepSeek` to `gpt-oss`), tool integrations, and framework implementations.
- **Automation & simplicity**: YAML-based configs, auto agent generation, and streamlined setup reduce manual overhead.

## 🌟 Benchmark Performance

`Youtu-agent` is built on open-source models and lightweight tools, demonstrating strong results on challenging deep search and tool use benchmarks.

- **[WebWalkerQA](https://huggingface.co/datasets/callanwu/WebWalkerQA)**: Achieved 60.71% accuracy with `DeepSeek-V3-0324`， using new released `DeepSeek-V3.1` can further improve to 71.47%, setting a new SOTA performance.
- **[GAIA](https://gaia-benchmark-leaderboard.hf.space/)**: Achieved 72.8% accuracy on the [text-only validation subset](https://github.com/sunnynexus/WebThinker/blob/main/data/GAIA/dev.json) using `DeepSeek-V3-0324` (including models used within tools). We are actively extending evaluation to the full GAIA benchmark with multimodal tools, and will release the trajectories in the near future. Stay tuned! ✨

![WebWalkerQA](docs/assets/images/benchmark_webwalkerqa.png)

## 💡 Examples

Click on the images to view detailed videos.

<table border="1" style="border-collapse: collapse;">
  <tr>
    <td style="border: 1px solid black; padding: 10px;">
      <a href="https://www.youtube.com/watch?v=SCR4Ru8_h5Q">
        <img src="https://img.youtube.com/vi/SCR4Ru8_h5Q/0.jpg" alt="Data Analysis" width="420" height="236">
      </a>
      <br><strong>Data Analysis</strong><br>Analyzes a CSV file and generates an HTML report.
    </td>
    <td style="border: 1px solid black; padding: 10px;">
      <a href="https://www.youtube.com/watch?v=GdA4AapE2L4">
        <img src="https://img.youtube.com/vi/GdA4AapE2L4/0.jpg" alt="File Management" width="420" height="236">
      </a>
      <br><strong>File Management</strong><br>Renames and categorizes local files for the user.
    </td>
  </tr>
  <tr>
    <td style="border: 1px solid black; padding: 10px;">
      <a href="https://www.youtube.com/watch?v=vBddCjjRk00">
        <img src="https://img.youtube.com/vi/vBddCjjRk00/0.jpg" alt="Wide Research" width="420" height="236">
      </a>
      <br><strong>Wide Research</strong><br>Gathers extensive information to generate a comprehensive report, replicating the functionality of Manus.
    </td>
    <td style="border: 1px solid black; padding: 10px;">
      <a href="https://www.youtube.com/watch?v=v3QQg0WAnPs">
        <img src="https://img.youtube.com/vi/v3QQg0WAnPs/0.jpg" alt="Paper Analysis" width="420" height="236">
      </a>
      <br><strong>Paper Analysis</strong><br>Parses a given paper, performs analysis, and compiles related literature to produce a final result.
    </td>
  </tr>
</table>

### 🤖 Automatic Agent Generation

A standout feature of `Youtu-agent` is its ability to **automatically generate agent configurations**. In other frameworks, defining a task-specific agent often requires writing code or carefully crafting prompts. In contrast, `Youtu-agent` uses simple YAML-based configs, which enables streamlined automation: a built-in "meta-agent" chats with you to capture requirements, then generates and saves the config automatically.

```bash
# Interactively clarify your requirements and auto-generate a config
python scripts/gen_simple_agent.py

# Run the generated config
python scripts/cli_chat.py --stream --config generated/xxx
```

<table border="1" style="border-collapse: collapse;">
  <tr>
    <td style="border: 1px solid black; width:420px; max-width:420px; word-break:break-word; overflow-wrap:anywhere; padding:10px; vertical-align:top;">
      <a href="https://www.youtube.com/watch?v=JVpHDJtKBo8">
        <img src="https://img.youtube.com/vi/JVpHDJtKBo8/0.jpg" alt="Automatic Agent Generation" width="420" height="236">
      </a>
      <br><strong>Automatic Agent Generation</strong><br>Interactively clarify your requirements, automatically generate the agent configuration, and run it right away.
    </td>
  </tr>
</table>


For more detailed examples and advanced use-cases, please refer to the [`examples`](./examples) directory and our comprehensive documentation at [`docs/examples.md`](./docs/examples.md).



## ✨ Features

![features](docs/assets/images/header.png)

### Design Philosophy
- **Minimal design**: We try to keep the framework simple and easy to use, avoiding unnecessary overhead.
- **Modular & configurable**: Flexible customization and easy integration of new components.
- **Open-source model support & low-cost**: Promotes accessibility and cost-effectiveness for various applications.

### Core Features
- **Built on openai-agents**: Leveraging the foundation of [openai-agents](https://github.com/openai/openai-agents-python) SDK, our framework inherits streaming, tracing, and agent-loop capabilities, ensuring compatibility with both `responses` and `chat.completions` APIs for seamless adaptation to diverse models like [gpt-oss](https://github.com/openai/gpt-oss).
- **Fully asynchronous**: Enables high-performance and efficient execution, especially beneficial for evaluating benchmarks.
- **Tracing & analysis system**: Beyond OTEL, our `DBTracingProcessor` system provides in-depth analysis of tool calls and agent trajectories. (will be released soon)

### Automation
- **YAML based configuration**: Structured and easily manageable agent configurations.
- **Automatic agent generation**: Based on user requirements, agent configurations can be automatically generated.
- **Tool generation & optimization**: Tool evaluation and automated optimization, and customized tool generation will be supported in the future.

### Use Cases
- **Deep / Wide research**: Covers common search-oriented tasks.
- **Webpage generation**: Examples include generating web pages based on specific inputs.
- **Trajectory collection**: Supports data collection for training and research purposes.


## 🤔 Why Choose Youtu-agent?

`Youtu-agent` is designed to provide significant value to different user groups:

### For Agents Researchers & LLM Trainers
- A **simple yet powerful baseline** that is stronger than basic ReAct, serving as an excellent starting point for model training and ablation studies.
- **One-click evaluation scripts** to streamline the experimental process and ensure consistent benchmarking.

### For Agent Application Developers
- A **proven and portable scaffolding** for building real-world agent applications.
- **Ease of Use**: Get started quickly with simple scripts and a rich set of built-in toolkits.
- **Modular Design**: Key components like `Environment` and `ContextManager` are encapsulated yet highly customizable.

### For AI & Agent Enthusiasts
- **Practical Use Cases**: The `/examples` directory includes tasks like deep research report generation, data analysis, and personal file organization.
- **Simplicity & Debuggability**: A rich toolset and visual tracing tools make development and debugging intuitive and straightforward.


## 🧩 Core Concepts

- **Agent**: An LLM configured with specific prompts, tools, and an environment.
- **Toolkit**: An encapsulated set of tools that an agent can use.
- **Environment**: The world in which the agent operates (e.g., a browser, a shell).
- **ContextManager**: A configurable module for managing the agent's context window.
- **Benchmark**: An encapsulated workflow for a specific dataset, including preprocessing, rollout, and judging logic.

For more design and implementation details, please refer to our [technical documentation](https://tencent.github.io/Youtu-agent/).

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
- [openai-agents](https://github.com/openai/openai-agents-python)
- [mkdocs-material](https://github.com/squidfunk/mkdocs-material)
- [model-context-protocol](https://github.com/modelcontextprotocol/python-sdk)

## Citation

If you find this work useful, please consider citing:

```bibtex
@misc{youtu-agent-2025,
  title={Youtu-agent: A Simple yet Powerful Agent Framework},
  author={Tencent Youtu Lab},
  year={2025},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/Tencent/Youtu-agent}},
}
```
