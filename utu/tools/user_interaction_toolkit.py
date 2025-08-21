from collections.abc import Callable
from typing import Any

from ..config import ToolkitConfig
from .base import AsyncBaseToolkit


class UserInteractionToolkit(AsyncBaseToolkit):
    def __init__(self, config: ToolkitConfig = None):
        super().__init__(config)

    async def ask_user(self, question: str) -> str:
        """Asks for user's input on a specific question

        Args:
            question (str): The question to ask.
        """
        return input(f"Please answer the question: {question}\n> ")

    async def final_answer(self, answer: Any) -> str:
        """Provides a final answer to the given problem.

        Args:
            answer (any): The answer to ask.
        """
        return answer

    async def get_tools_map(self) -> dict[str, Callable]:
        return {
            "ask_user": self.ask_user,
            "final_answer": self.final_answer,
        }
