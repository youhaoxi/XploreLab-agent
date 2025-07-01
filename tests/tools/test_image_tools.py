import pytest

from utu.tools.image_toolkit import ImageToolkit
from utu.config import ConfigLoader, ToolkitConfig

@pytest.fixture
def config() -> ToolkitConfig: 
    config = ConfigLoader.load_toolkit_config("image")
    return config

@pytest.fixture
def image_toolkit(config: ToolkitConfig) -> ImageToolkit:
    return ImageToolkit(config=config.config)

image_url1 = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
tasks = (
    (image_url1, "What is main colors of this image?"),
    (image_url1, )
)

async def test_image_toolkit(image_toolkit: ImageToolkit):
    for task in tasks:
        result = await image_toolkit.image_qa(*task)
        print(f"{task}: {result}")