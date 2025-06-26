from utu.config import ConfigLoader, ToolkitConfig

def test_load_subconfig():
    config = ConfigLoader._load_config_to_dict("examples/mcp")
    print(config)

def test_load_config():
    config = ConfigLoader.load_config("default")
    print(config)

def test_load_toolkit_config():
    config = ConfigLoader.load_toolkit_config("memory")
    print(config)
