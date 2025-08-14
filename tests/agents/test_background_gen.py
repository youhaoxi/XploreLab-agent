from utu.ww.utils.background_gen import ModuleGenBackground

background_gen = ModuleGenBackground()

queries = (
    "对比一下小米su7和yu7",
    "请针对伊朗和以色列的战争，提供一个深度的分析报告",
    "上海天气",
    "帮我总结 金字塔原理 这本书的核心内容，说明每个章节的重点内容",
    "请针对伊朗和以色列的战争，提供一个深度的分析报告",
)


async def test_ww_background():
    for q in queries:
        print(f"query: {q}")
        res = await background_gen.generate_background_info(q)
        print(res)
