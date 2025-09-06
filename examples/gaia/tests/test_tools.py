import asyncio

from examples.gaia.tools.code_execution_toolkit import CodeExecutionToolkit
from examples.gaia.tools.excel_toolkit import ExcelToolkit
from utu.config import ConfigLoader


async def test_excel_toolkit():
    excel_toolkit = ExcelToolkit()

    res = await excel_toolkit.extract_excel_content(
        "data/gaia/2023/validation/3da89939-209c-4086-8520-7eb734e6b4ef.xlsx"
    )
    print(res)


async def test_code_execution_toolkit():
    config = ConfigLoader.load_toolkit_config("arxiv")
    config.config = {"working_dir": "workspace/"}
    code_execution_toolkit = CodeExecutionToolkit(config)

    res = await code_execution_toolkit.execute_code("print('hello world')")
    print(f"> res: {res}")


if __name__ == "__main__":
    # asyncio.run(test_excel_toolkit())
    asyncio.run(test_code_execution_toolkit())
