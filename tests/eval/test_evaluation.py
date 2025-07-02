from utu.config import ConfigLoader
from utu.eval.evaluation import MixedEval
from utu.eval.data_manager.file_data_manager import FileDataManager

config = ConfigLoader.load_eval_config("default")
sources = {"GAIA", "BrowseComp", "BrowseComp_ZH", "XBench"}
evaluator = MixedEval(sources, config)
data_manager = FileDataManager(config)

async def test_mixed_eval():
    _ = await data_manager.load_dataset()
    data_run, data_to_rollout = await data_manager.load_data_to_rollout()
    judged_data, result = await evaluator.eval(data_run)
    print(result)
