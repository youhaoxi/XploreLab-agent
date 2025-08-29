# <img src="docs/assets/logo.svg" alt="Youtu-agent Logo" height="24px"> Youtu-agent: 一个简单而强大的智能体框架

<div align="center">
<a href="https://tencent.github.io/Youtu-agent/"><img src=https://img.shields.io/badge/📖-文档-blue.svg></a>
<!-- <a href=https://arxiv.org/abs/2502.14345><img src=https://img.shields.io/badge/arXiv-2502.14345-b31b1b.svg></a> -->
<a href=https://github.com/Tencent/Youtu-agent><img src=https://img.shields.io/badge/GitHub-腾讯-blue.svg></a>
<a href=https://deepwiki.com/Tencent/Youtu-agent><img src=https://img.shields.io/badge/DeepWiki-Tencent-blue.svg></a>
</div>

<p align="center">
| <a href="README.md"><b>English</b></a>
| <a href="#-基准性能"><b>🌟 性能</b></a> 
| <a href="#-示例"><b>💡 示例</b> </a> 
| <a href="#-特性"><b>✨ 特性</b> </a> 
| <a href="#-快速开始"><b>🚀 快速开始</b> </a> 
| 
</p>


`Youtu-agent` 是一个灵活、高性能的框架，用于构建、运行和评估自主智能体。除了在基准测试中名列前茅，该框架还提供了强大的智能体能力，例如数据分析、文件处理和深度研究。

<img src="docs/assets/mascot.png" alt="Youtu-agent Logo" width="200" align="left" style="margin-right:20px;">

主要亮点：
- **验证性能**：在 WebWalkerQA 上达到 71.47% 的 pass@1，在 GAIA（纯文本子集）上达到 72.8% 的 pass@1，纯粹使用 `DeepSeek-V3` 系列模型（不使用 Claude 或 GPT），建立了强大的开源起点。
- **开源友好且成本敏感**：针对可访问、低成本部署进行了优化，不依赖封闭模型。
- **实际用例**：开箱即用地支持 CSV 分析、文献综述、个人文件整理以及播客和视频生成等任务。（即将推出）
- **灵活的架构**：基于 [openai-agents](https://github.com/openai/openai-agents-python) 构建，可兼容各种模型 API（从 `DeepSeek` 到 `gpt-oss`）、工具集成和框架实现。
- **自动化与简洁性**：基于 YAML 的配置、自动智能体生成和简化的设置减少了手动开销。

## 🗞️ 新闻

- [2025-08-28] 我们发布了 DeepSeek-V3.1 的更新，并介绍了如何在 `Youtu-agent` 框架中应用它。[这里](https://doc.weixin.qq.com/doc/w3_AcMATAZtAPICNvcLaY5FvTOuo7MwF) 是文档。

## 🌟 基准性能

`Youtu-agent` 基于开源模型和轻量级工具构建，在具有挑战性的深度搜索和工具使用基准测试中表现出色。

- **[WebWalkerQA](https://huggingface.co/datasets/callanwu/WebWalkerQA)**：使用 `DeepSeek-V3-0324` 实现了 60.71% 的准确率，使用新发布的 `DeepSeek-V3.1` 可进一步提升至 71.47%，创造了新的 SOTA 性能。
- **[GAIA](https://gaia-benchmark-leaderboard.hf.space/)**：使用 `DeepSeek-V3-0324`（包括工具中使用的模型）在[纯文本验证子集](https://github.com/sunnynexus/WebThinker?tab=readme-ov-file#benchmarks)上实现了 72.8% 的 pass@1。我们正在积极扩展对带有多模态工具的完整 GAIA 基准的评估，将在近期放出完整轨迹，敬请关注！✨

![WebWalkerQA](docs/assets/images/benchmark_webwalkerqa.png)

## 💡 使用示例

<table border="1" style="border-collapse: collapse;">
  <tr>
    <td style="border: 1px solid black; padding: 10px;">
      <a href="https://www.youtube.com/watch?v=SCR4Ru8_h5Q">
        <img src="https://img.youtube.com/vi/SCR4Ru8_h5Q/0.jpg" alt="Data Analysis" width="420" height="236">
      </a>
      <br><strong>数据分析</strong><br>分析 CSV 文件并生成 HTML 报告。
    </td>
    <td style="border: 1px solid black; padding: 10px;">
      <a href="https://www.youtube.com/watch?v=GdA4AapE2L4">
        <img src="https://img.youtube.com/vi/GdA4AapE2L4/0.jpg" alt="File Management" width="420" height="236">
      </a>
      <br><strong>文件管理</strong><br>为用户重命名和分类本地文件。
    </td>
  </tr>
  <tr>
    <td style="border: 1px solid black; padding: 10px;">
      <a href="https://www.youtube.com/watch?v=vBddCjjRk00">
        <img src="https://img.youtube.com/vi/vBddCjjRk00/0.jpg" alt="Wide Research" width="420" height="236">
      </a>
      <br><strong>广度研究</strong><br>收集大量信息以生成综合报告，复刻 Manus 的功能。
    </td>
    <td style="border: 1px solid black; padding: 10px;">
      <a href="https://www.youtube.com/watch?v=v3QQg0WAnPs">
        <img src="https://img.youtube.com/vi/v3QQg0WAnPs/0.jpg" alt="Paper Analysis" width="420" height="236">
      </a>
      <br><strong>论文分析</strong><br>解析给定论文，进行分析，并整理相关文献以得出最终结果。
    </td>
  </tr>
</table>

### 🤖 自动智能体生成

`Youtu-agent`的突出优势在于其**自动化生成智能体及其配置**的能力。在其他框架中，定义特定任务的智能体通常需要编写代码或是精心设计提示词，而`Youtu-agent`采用基于 YAML 的简洁配置方案，实现了高效自动化：内置的“元智能体”与用户对话并捕获需求，然后自动生成并保存配置。

```bash
# Interactively clarify your requirements and auto-generate a config
python scripts/gen_simple_agent.py

# Run the generated config
python scripts/cli_chat.py --stream --config generated/xxx
```

<table border="1" style="border-collapse: collapse;">
  <tr>
    <td style="border: 1px solid black; width:420px; padding:10px; vertical-align:top;">
      <a href="https://www.youtube.com/watch?v=JVpHDJtKBo8">
        <img src="https://img.youtube.com/vi/JVpHDJtKBo8/0.jpg" alt="Automatic Agent Generation" width="420" height="236">
      </a>
      <br><strong>自动智能体生成</strong><br>交互式对话的方式捕获需求，自动生成agent配置，并立即运行。
    </td>
  </tr>
</table>


更详细的示例和高级用例，请参阅 [`examples`](./examples) 目录和我们的文档 [`docs/examples.md`](./docs/examples.md)。

## ✨ 特性

![features](docs/assets/images/header.png)

### 设计理念
- 极简设计：这确保了框架的精简，避免了不必要的开销。
- 模块化与可配置：这允许灵活的定制和新组件的轻松集成。
- 开源模型支持与低成本：这促进了各种应用的可访问性和成本效益。

### 核心功能
- 基于openai-agents构建：利用 [openai-agents](https://github.com/openai/openai-agents-python) SDK 作为基础，我们的框架继承了 streaming、tracing 和 agent-loop 能力，确保了与 `responses` 和 `chat.completions` API 的兼容性，无缝适应 [gpt-oss](https://github.com/openai/gpt-oss) 等多样化模型。
- 完全异步：这实现了高性能和高效执行，尤其有利于高效的评估。
- 追踪与分析系统：除了 OTEL，我们的 `DBTracingProcessor` 系统提供了对工具调用和智能体轨迹的深入分析。（即将发布）

### 自动化
- 基于 YAML 的配置：这允许结构化且易于管理的智能体配置。
- 自动智能体生成：根据用户需求，可以自动生成智能体配置。
- 工具生成与优化：工具评估和自动化优化，定制化工具生成的能力将在未来得到支持。

### 用例
- 深度/广度研究：涵盖常见的面向搜索的任务。
- 网页生成：示例包括根据特定输入生成网页。
- 轨迹收集：支持用于训练和研究目的的数据收集。

## 🤔 为何选择 Youtu-agent？

`Youtu-agent` 旨在为不同的用户群体提供价值：

### 对于智能体研究人员和大型语言模型训练师
- 一个**简单而强大的基线**，比基本的 ReAct 更强大，可作为模型训练和消融研究的绝佳起点。
- **一键评估脚本**用以简化实验过程，并确保一致的基准测试。

### 对于智能体应用开发者
- 一个**经过验证且可移植的脚手架**，用于构建真实的智能体应用程序。
- **易于使用**：通过简单的脚本和丰富的内置工具包快速上手。
- **模块化设计**：`Environment` 和 `ContextManager` 等关键组件被封装，但高度可定制。

### 对于人工智能和智能体爱好者
- **实际用例**：`/examples` 目录包含深度研究报告生成、数据分析和个人文件整理等任务。
- **简单性与可调试性**：丰富的工具集和可视化追踪工具使开发和调试直观而直接。

## 🧩 核心概念

- **智能体（Agent）**：一个配置了提示词、工具和环境的大语言模型。
- **工具包（Toolkit）**：智能体可以使用的封装工具集。
- **环境（Environment）**：智能体操作的世界（例如，浏览器、shell）。
- **上下文管理器（ContextManager）**：一个可配置模块，用于管理智能体的上下文窗口。
- **基准（Benchmark）**：一个针对特定数据集的封装工作流，包括预处理、执行和判断逻辑。

更多的设计与实现细节，请参阅我们的[在线文档](https://tencent.github.io/Youtu-agent/)。

## 🚀 快速上手

Youtu-agent 提供了完整的代码与示例，帮助你快速开始使用。按照以下步骤即可运行你的第一个智能体：

### 环境准备

克隆仓库并安装依赖：

```bash
git clone https://github.com/Tencent/Youtu-agent.git
cd Youtu-agent
uv sync
source ./.venv/bin/activate
cp .env.example .env  # 配置相关环境变量...
```

> [!NOTE]
> 本项目使用 **Python 3.12+**。推荐使用 [uv](https://github.com/astral-sh/uv) 进行依赖管理。

### 快速开始

Youtu-agent 内置了配置文件。例如，默认配置文件 (`configs/agents/default.yaml`) 定义了一个带有搜索工具的简单 Agent：

```yaml
defaults:
  - /model/base
  - /tools/search@toolkits.search
  - _self_

agent:
  name: simple-tool-agent
  instructions: "You are a helpful assistant that can search the web."
```

你可以通过以下命令启动交互式 CLI 聊天机器人：

```bash
python scripts/cli_chat.py --stream --config default
```

📖 更多内容请参考：[快速开始文档](https://tencent.github.io/Youtu-agent/quickstart)

### 示例探索

本仓库提供了多个可直接运行的示例。例如，你可以基于某个研究主题自动生成一张 **SVG 信息图**：

```bash
python examples/svg_generator/main_web.py
```

> [!NOTE]
> 要使用 WebUI，你需要安装 `utu_agent_ui` 包。参考 [文档](https://tencent.github.io/Youtu-agent/frontend/#installation)。

给定一个研究主题后，Agent 会自动执行网络搜索，收集相关信息，并输出一张 SVG 可视化图。

![svg_generator_ui](https://github.com/user-attachments/assets/337d327f-91ee-434e-bbcf-297dd4b26c28)

![svg_generator_result](https://github.com/user-attachments/assets/41aa7348-5f02-4daa-b5b2-225e35d21067)

📖 更多示例请参考：[示例文档](https://tencent.github.io/Youtu-agent/examples)

### 运行评测

Youtu-agent 还支持在标准数据集上进行基准测试。例如，在 **WebWalkerQA** 上运行评测：

```bash
# 数据集预处理
python scripts/data/process_web_walker_qa.py

# 使用配置 ww.yaml 运行评测
python scripts/run_eval.py --config_name ww --exp_id <your_exp_id> --dataset WebWalkerQA --concurrency 5
```

结果会保存到本地，并可在分析平台中进一步查看。

![eval_analysis_overview](https://github.com/user-attachments/assets/4a285b9e-d096-437e-9b8e-e5bf6b1924b6)

![eval_analysis_detail](https://github.com/user-attachments/assets/4ede525a-5e16-4d88-9ebb-01a7dca3aaec)

📖 更多内容请参考：[评测文档](https://tencent.github.io/Youtu-agent/eval)

## 🙏 致谢

本项目基于以下优秀开源项目：
- [openai-agents](https://github.com/openai/openai-agents-python)
- [mkdocs-material](https://github.com/squidfunk/mkdocs-material)
- [model-context-protocol](https://github.com/modelcontextprotocol/python-sdk)

## 📚 引用

如果您觉得这项工作有帮助，请考虑引用：

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

## ⭐ Star History

![Star History Chart](https://api.star-history.com/svg?repos=Tencent/Youtu-agent&type=Date)
