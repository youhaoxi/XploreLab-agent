from utu.config import ConfigLoader

def test_load_subconfig():
    config = ConfigLoader._load_config_to_dict("agents/tools/memory")
    print(config)

def test_load_model_config():
    config = ConfigLoader.load_model_config("base")
    print(config)

def test_load_toolkit_config():
    config = ConfigLoader.load_toolkit_config("memory")
    print(config)

def test_load_agent_config():
    config = ConfigLoader.load_agent_config("v00")
    config = ConfigLoader.load_agent_config("default")
    config = ConfigLoader.load_agent_config("examples/mcp")
    config = ConfigLoader.load_agent_config("examples/eval")
    print(config)

def test_load_eval_config():
    config = ConfigLoader.load_eval_config("v00")
    print(config)
