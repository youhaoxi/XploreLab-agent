import asyncio

from examples.gaia.tools.excel_toolkit import ExcelToolkit

excel_toolkit = ExcelToolkit()


async def test_excel_toolkit():
    res = await excel_toolkit.extract_excel_content(
        "data/gaia/2023/validation/3da89939-209c-4086-8520-7eb734e6b4ef.xlsx"
    )
    print(res)


if __name__ == "__main__":
    asyncio.run(test_excel_toolkit())
