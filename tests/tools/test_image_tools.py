import pytest

from utu.tools import ImageToolkit
from utu.config import ConfigLoader


@pytest.fixture
def image_toolkit() -> ImageToolkit:
    config = ConfigLoader.load_toolkit_config("image")
    return ImageToolkit(config=config)

image_url1 = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
tasks = (
    (image_url1, "What is main colors of this image?"),
    (image_url1, )
)

async def test_image_toolkit(image_toolkit: ImageToolkit):
    for task in tasks:
        result = await image_toolkit.image_qa(*task)
        print(f"{task}: {result}")
