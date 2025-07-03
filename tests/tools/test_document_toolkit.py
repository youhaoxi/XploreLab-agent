import pytest

from utu.tools import DocumentToolkit
from utu.config import ConfigLoader


@pytest.fixture
def document_toolkit() -> DocumentToolkit:
    config = ConfigLoader.load_toolkit_config("document")
    return DocumentToolkit(config=config.config)

document_url1 = "https://arxiv.org/pdf/2107.14339"
tasks = (
    (document_url1, "There is a diagram of an X-ray time profile in this document. How long is the time profile (in seconds)?"),
    (document_url1, )
)

async def test_document_toolkit(document_toolkit: DocumentToolkit):
    # res = await document_toolkit.parse_document(document_url1)
    # print(res)
    for task in tasks:
        result = await document_toolkit.document_qa(*task)
        print(f"{task}: {result}")