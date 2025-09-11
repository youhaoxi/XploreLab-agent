from utu.ui.webui_agents import WebUIAgents

DEFAULT_CONFIG = "base.yaml"

if __name__ == "__main__":
    webui = WebUIAgents(default_config=DEFAULT_CONFIG)
    webui.launch()
