""" 
@smolagents/examples/open_deep_research/scripts/visual_qa.py
@camel/camel/toolkits/image_analysis_toolkit.py
https://platform.openai.com/docs/guides/images-vision?api-mode=chat
"""
from typing import Optional, Callable
from io import BytesIO
import requests
import base64

from urllib.parse import urlparse
from PIL import Image

from .base import AsyncBaseToolkit
from ..utils import SimplifiedAsyncOpenAI, get_logger
from ..config import ToolkitConfig

logger = get_logger(__name__)

# ref @camel
SP_DESCRIPTION = """You are an image analysis expert. Provide a detailed description including text if present."""

SP_INSTRUCTION = """Answer questions about images by:
1. Careful visual inspection
2. Contextual reasoning
3. Text transcription where relevant
4. Logical deduction from visual evidence"""


class ImageToolkit(AsyncBaseToolkit):
    def __init__(self, config: ToolkitConfig = None) -> None:
        super().__init__(config)
        self.llm = SimplifiedAsyncOpenAI(**self.config.config_llm.model_provider.model_dump())

    def _load_image(self, image_path: str) -> str:
        parsed = urlparse(image_path)
        image: Image.Image = None

        if parsed.scheme in ("http", "https"):
            logger.debug(f"Fetching image from URL: {image_path}")
            try:
                response = requests.get(image_path, timeout=15)
                response.raise_for_status()
                image = Image.open(BytesIO(response.content)).convert("RGB")
            except requests.exceptions.RequestException as e:
                logger.error(f"URL fetch failed: {e}")
                raise
        else:
            logger.debug(f"Loading local image: {image_path}")
            try:
                image = Image.open(image_path).convert("RGB")
            except Exception as e:
                logger.error(f"Image loading failed: {e}")
                raise ValueError(f"Invalid image file: {e}")
        # Convert the image to a base64 string
        buffer = BytesIO()
        image.save(buffer, format="JPEG")  # Use the appropriate format (e.g., JPEG, PNG)
        base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

        # add string formatting required by the endpoint
        image_string = f"data:image/jpeg;base64,{base64_image}"
        return image_string

    async def image_qa(self, image_path: str, question: Optional[str] = None) -> str:
        """Generate textual description or answer questions about attached image.
        
        Args:
            image_path (str): Local path or URL to an image.
            question (str, optional): The question to answer. If not provided, a description of the image will be generated.
        """
        image_str = self._load_image(image_path)
        if not question:
            messages = [
                {"role": "system", "content": SP_DESCRIPTION},
                {"role": "user", "content": [{"type": "image_url", "image_url": {"url": image_str}}]}
            ]
            output = await self.llm.query_one(messages=messages, **self.config.config_llm.model_params.model_dump())
            output = f"You did not provide a particular question, so here is a detailed caption for the image: {output}"
        else:
            messages = [
                {"role": "system", "content": SP_DESCRIPTION},
                {"role": "user", "content": [{"type": "text", "text": question}, {"type": "image_url", "image_url": {"url": image_str}}]}
            ]
            output = await self.llm.query_one(messages=messages, **self.config.config_llm.model_params.model_dump())
        return output

    async def get_tools_map(self) -> dict[str, Callable]:
        return {
            "visualizer": self.image_qa,
        }