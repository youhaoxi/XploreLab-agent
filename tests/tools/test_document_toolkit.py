import pytest

from utu.tools import DocumentToolkit
from utu.config import ConfigLoader


@pytest.fixture
def document_toolkit() -> DocumentToolkit:
    config = ConfigLoader.load_toolkit_config("document")
    return DocumentToolkit(config=config)

document_url1 = "https://arxiv.org/pdf/2107.14339.pdf"
document_path = "/Users/frankshi/LProjects/Agents/uTu-agent/data/gaia/files/3cc53dbf-1ab9-4d21-a56a-fc0151c10f89.xlsx"
tasks = (
    (document_url1, "There is a diagram of an X-ray time profile in this document. How long is the time profile (in seconds)?"),
    (document_url1, ),
    (document_path, ),
)

async def test_document_toolkit(document_toolkit: DocumentToolkit):
    # res = await document_toolkit.parse_document(document_url1)
    # print(res)
    for task in tasks:
        result = await document_toolkit.document_qa(*task)
        print(f"{task}: {result}")
