from importlib import import_module

def get_benchmark_templates(benchmark_name: str) -> dict:
    """Get the benchmark templates for a given benchmark name."""
    try:
        module = import_module(f"utu.eval.processer.prompts.{benchmark_name}")
        return {
            "system": getattr(module, "SYSTEM_PROMPT", ""),
            "augmented": getattr(module, "AUGMENTED_TEMPLATE", ""),
            "judge": getattr(module, "JUDGE_TEMPLATE", ""),
        }
    except ImportError:
        print(f"Benchmark '{benchmark_name}' not found. Using default templates.")
        module = import_module("utu.eval.processer.prompts.default")
        return {
            "system": getattr(module, "SYSTEM_PROMPT", ""),
            "augmented": getattr(module, "AUGMENTED_TEMPLATE", ""),
            "judge": getattr(module, "JUDGE_TEMPLATE", ""),
        }

__all__ = [
    "get_benchmark_templates",
]
