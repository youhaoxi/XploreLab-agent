"""
Workflow based implementation of a search agent
  1. query decomposition
  2. web search
  3. web result summarization
  4. query summarization
"""
import json
import asyncio
from pydantic import BaseModel
from openai import AsyncOpenAI

from .utils import Base, SearchResult
from ..config import AgentConfig
from .simple_agent import SimpleAgent
from ..eval.common import get_trajectory_from_agent_result
from ..tools import TOOLKIT_MAP

'''
class SearchResult(BaseModel):
    trace_id: str
    """ The session ID for the search run, useful for tracking and debugging."""

    final_output: str
    """ The final output of the search agent after processing the query and summarizing results."""

    trajectory: list[dict]
    """ The trajectory of the search agent."""

    search_results: list[dict]
    """ The list of search results obtained during the search process."""
'''

class SearcherAgent(Base):
    """
    A worklfow-based search agent that decomposes a query, searches the web for sub-queries,
    summarizes the results, and provides a final analysis.
    """
    llm: AsyncOpenAI = None  # OpenAI client for LLM calls
    trajectory: list[dict] = None  # Track tool calls and results

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.trajectory = []

    def build(self):
        """ Build tools for the search agent. """
        for tool_name, tool_config in self.config.toolkits.items():
            if tool_name in TOOLKIT_MAP:
                tool_class = TOOLKIT_MAP[tool_name]
                tool_instance = tool_class(tool_config)
                setattr(self, tool_name, tool_instance)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")

    # TODO: add background information
    async def research(self, query: str, background: str = None, trace_id: str = None) -> SearchResult:
        """ Run the search agent with a given query.
        
        This method will:
        1. Decompose the query into sub-queries
        2. Perform web searches for each sub-query
        3. Summarize the search results
        4. Provide a final analysis of the query based on the summaries

        :param query: The query to run the agent on
        :return: SearchRunResult containing the final output, trajectory, and search results
        """
        background = background or ""
        # 1. Decompose the query into sub-queries
        sub_queries = await self.decompose_query(query, background)

        # 2. Perform web searches for each sub-query
        search_results = []
        sub_answers = []
        tasks = []
        self._init_sub_trajectories(len(sub_queries))
        # run multiple tasks concurrently
        for i, sub_query in enumerate(sub_queries):
            tasks.append(self.research_one(sub_query, background, i))
        results = await asyncio.gather(*tasks)
        # Sort results by index to maintain order
        results.sort(key=lambda x: x[2])  # Sort by index
        for search_result, sub_answer, task_index in results:
            search_results.extend([*search_result, sub_answer])
            sub_answers.append(sub_answer)
            # Merge sub-trajectories in order
            task_id = f"sub_query_{task_index}"
            if hasattr(self, '_sub_trajectories') and task_id in self._sub_trajectories:
                self.trajectory.extend(self._sub_trajectories[task_id])

        # 3. Summarize and analyze the search results
        final_output = await self.summarize_final_output(query, background, sub_answers)

        # Clean up temporary sub-trajectories
        self._cleanup_sub_trajectories()

        return SearchResult(
            # trace_id=self.trace_id,
            output=final_output,
            trajectory=self._get_trajectory(),
            search_results=search_results
        )
    
    async def research_one(self, sub_query: str, background: str, index: int) -> tuple[list[dict], dict, int]:
        """ Research a single sub-query and return the search results and summary.
        
        :param sub_query: The sub-query to research
        :param background: The background information to use for the search
        :param index: The index to maintain order
        :return: A tuple containing search results, summary, index
        """
        task_id = f"sub_query_{index}"
        
        # Perform web search for the sub-query with asyncio.Semaphore
        search_results = await self.perform_web_search(sub_query, background, task_id)
        # Summarize the search results
        summary = await self.summarize_sub_search_results(sub_query, background, search_results, task_id)
        
        return search_results, {"sub_query": sub_query, "summary": summary}, index
    
    async def _call_tool(self, tool_name: str, method_name: str, arguments: dict, task_id: str = None, *args, **kwargs):
        """ Universal tool calling method with trajectory recording.
        
        :param tool_name: Name of the tool attribute
        :param method_name: Name of the method to call
        :param arguments: Arguments dict for trajectory logging
        :param task_id: Task identifier for ordering trajectory items
        :param args: Positional arguments to pass to the method
        :param kwargs: Keyword arguments to pass to the method
        :return: Result from the tool method
        """
        # Record tool call
        tool_call = {
            "role": "assistant",
            "tool_calls": [{"name": method_name, "arguments": json.dumps(arguments, ensure_ascii=False)}]
        }
        self._add_to_trajectory(tool_call, task_id)
        
        # Check if tool exists and call it
        if hasattr(self, tool_name):
            tool = getattr(self, tool_name)
            result = await tool.run(*args, **kwargs)
            
            tool_result = {
                "role": "tool",
                "content": result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
            }
            self._add_to_trajectory(tool_result, task_id)
            
            return result
        else:
            error_msg = f"{method_name} tool is not available."
            tool_result = {
                "role": "tool",
                "content": f"Error: {error_msg}"
            }
            self._add_to_trajectory(tool_result, task_id)
            raise NotImplementedError(error_msg)

    async def decompose_query(self, query: str, background: str) -> list[str]:
        """ Decompose the query into sub-queries.
        
        :param query: The query to decompose
        :param background: The background information to use for decomposition
        :return: A list of sub-queries
        """
        return await self._call_tool(
            tool_name="query_decomposer",
            method_name="decompose_query", 
            arguments={"query": query},
            query=query,
            background=background
        )

    async def perform_web_search(self, sub_query: str, background: str, task_id: str = None) -> list[str]:
        """ Perform a web search for the given sub-query.
        
        :param sub_query: The sub-query to search for
        :param background: The background information to use for the search
        :param task_id: Task identifier for trajectory ordering
        :return: A list of search results
        """
        return await self._call_tool(
            tool_name="web_searcher",
            method_name="web_search",
            arguments={"query": sub_query},
            task_id=task_id,
            query=sub_query,
            background=background
        )

    async def summarize_sub_search_results(self, sub_query: str, background: str, search_results: list[str], task_id: str = None) -> str:
        """ Summarize the search results for a sub-query.
        
        :param sub_query: The sub-query
        :param background: The background information to use for summarization
        :param search_results: The list of search results to summarize
        :param task_id: Task identifier for trajectory ordering
        :return: A summary of the search results
        """
        return await self._call_tool(
            tool_name="summarizer",
            method_name="summarize",
            arguments={"query": sub_query, "results_count": len(search_results)},
            task_id=task_id,
            query=sub_query,
            background=background,
            search_results=search_results
        )
    
    async def summarize_final_output(self, query: str, background: str, sub_answers: list[str]) -> str:
        """ Summarize the final output based on sub-answers.
        
        :param query: The original query
        :param background: The background information to use for summarization
        :param sub_answers: The list of summaries from sub-queries
        :return: The final output summarizing the entire search process
        """
        return await self._call_tool(
            tool_name="summarizer",
            method_name="summarize",
            arguments={"query": query, "sub_answers_count": len(sub_answers)},
            query=query,
            background=background,
            search_results=sub_answers
        )
    
    def _init_sub_trajectories(self, num_sub_queries: int):
        """ Pre-create sub-trajectory structure """
        self._sub_trajectories = {}
        for i in range(num_sub_queries):
            task_id = f"sub_query_{i}"
            self._sub_trajectories[task_id] = []
    
    def _cleanup_sub_trajectories(self):
        """ Clean up temporary sub-trajectories """
        if hasattr(self, '_sub_trajectories'):
            delattr(self, '_sub_trajectories')
    
    def _add_to_trajectory(self, item: dict, task_id: str = None):
        """ Add an item to the appropriate trajectory based on task_id.
        
        :param item: The trajectory item to add
        :param task_id: Task identifier, if None or "main", adds to main trajectory
        """
        # Add task_id if not present
        if "task_id" not in item:
            item["task_id"] = task_id or "main"
        
        # Determine where to store the item
        if task_id and task_id != "main":
            # Store in sub-trajectory (structure already created)
            self._sub_trajectories[task_id].append(item)
        else:
            # Store in main trajectory
            self.trajectory.append(item)
    
    def _get_trajectory(self) -> list[dict]:
        """ Get the trajectory of the search agent.
        
        :return: A list of dictionaries representing the trajectory
        """
        return self.trajectory
