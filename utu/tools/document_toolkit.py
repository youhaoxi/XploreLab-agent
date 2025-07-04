""" 
https://github.com/lumina-ai-inc/chunkr
"""

from typing import Optional, Callable
import logging
import os

from chunkr_ai import Chunkr
from chunkr_ai.models import Configuration

from .base import AsyncBaseToolkit
from ..config import ToolkitConfig
from ..utils import async_file_cache, oneline_object, SimplifiedAsyncOpenAI

logger = logging.getLogger("utu")


# ref @smolagents
SP = """You will have to write a short caption for this file, then answer question based on the file content."""

INSTRUCTION_QA = r"""Now answer the question below. Use these three headings: '1. Short answer', '2. Extremely detailed answer', '3. Additional Context on the document and question asked'.
Question: {question}"""
INSTRUCTION_SUMMARY = r"""Please provide a structured description of the document, including important informations, e.g. author, date, title, keywords, summary, key points, etc."""

class DocumentToolkit(AsyncBaseToolkit):
    def __init__(self, config: ToolkitConfig = None) -> None:
        super().__init__(config)
        self.chunkr = Chunkr(api_key=os.getenv("CHUNKR_API_KEY"))
        self.chunkr.config = Configuration(
            high_resolution=self.config.config.get("high_resolution", True),
        )
        self.text_limit = self.config.config.get("text_limit", 100_000)
        self.llm = SimplifiedAsyncOpenAI(**self.config.config_llm.model_dump())
    
    @async_file_cache(expire_time=None)
    async def parse_document(self, document_path: str) -> str:
        # https://docs.chunkr.ai/sdk/data-operations/create#supported-file-types
        logger.info(f"[tool] parse_document: {oneline_object(document_path)}")
        task = await self.chunkr.upload(document_path)

        logger.info(f"  getting results...")
        markdown = task.markdown()
        # html = task.html()
        # content = task.content()
        # json = task.json()

        # self.chunkr.close()
        return markdown

    async def document_qa(self, document_path: str, question: Optional[str] = None) -> str:
        """Get file content summary or answer questions about attached document.
        Supported file types: pdf, docx, pptx, xlsx, xls, ppt, doc
        
        Args:
            document_path (str): Local path or URL to a document.
            question (str, optional): The question to answer. If not provided, a description of the document will be generated.
        """
        document_markdown = await self.parse_document(document_path)
        if len(document_markdown) > self.text_limit:
            document_markdown = document_markdown[:self.text_limit] + "\n..."
        messages = [
            {"role": "system", "content": SP},
            {"role": "user", "content": document_markdown},
        ]
        if question:
            messages.append({"role": "user", "content": INSTRUCTION_QA.format(question=question)})
        else:
            messages.append({"role": "user", "content": INSTRUCTION_SUMMARY})
        output = await self.llm.query_one(messages=messages)
        if not question:
            output = f"You did not provide a particular question, so here is a detailed caption for the document: {output}"
        return output

    async def get_tools_map(self) -> dict[str, Callable]:
        return {
            "document_qa": self.document_qa,
        }
