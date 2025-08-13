from utu.agents import SimpleAgent
from utu.config import ConfigLoader
from utu.tools import SearchToolkit


def get_tools():
    toolkit = SearchToolkit(ConfigLoader.load_toolkit_config("search"))
    return toolkit.get_tools_in_agents_sync()


INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you search the web for that term and "
    "produce a concise summary of the results. The summary must be 2-3 paragraphs and less than 300 "
    "words. Capture the main points. Write succinctly, no need to have complete sentences or good "
    "grammar. This will be consumed by someone synthesizing a report, so its vital you capture the "
    "essence and ignore any fluff. Do not include any additional commentary other than the summary "
    "itself."
)

search_agent = SimpleAgent(
    name="Search agent",
    instructions=INSTRUCTIONS,
    tools=get_tools(),
)
