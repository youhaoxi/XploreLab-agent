import pytest

from utu.tools import FileEditToolkit

DIFF = """<<<<<<< SEARCH
line 1
=======
line 1 edited!
>>>>>>> REPLACE"""


@pytest.fixture
def file_edit_toolkit():
    return FileEditToolkit(
        config={
            "work_dir": "/tmp/",
            "backup_enabled": True,
            "default_encoding": "utf-8",
        }
    )


async def test_edit_file(file_edit_toolkit: FileEditToolkit):
    result = await file_edit_toolkit.edit_file("test.txt", DIFF)
    print(result)
