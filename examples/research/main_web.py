from __future__ import annotations

import asyncio

from agents import custom_span, gen_trace_id, trace
from rich.console import Console

import agents as ag

from utu.agents.orchestra.common import OrchestraStreamEvent, CreatePlanResult, WorkerResult, AnalysisResult
from .agents.planner_agent import WebSearchItem, WebSearchPlan, planner_agent
from .agents.search_agent import search_agent
from .agents.writer_agent import ReportData, writer_agent
from utu.ui.webui_chatbot import WebSocketHandler, WebUIChatbot

class ResearchManager:
    def __init__(self):
        self.console = Console()
        
    async def run_streamed(self, query: str) -> None:
        search_plan = await self._plan_searches(query)
        yield OrchestraStreamEvent(
            name="plan",
            item=CreatePlanResult(
                analysis=search_plan,
                todo="",
            ),
        )
        search_results = await self._perform_searches(search_plan)
        yield OrchestraStreamEvent(
            name="worker",
            item=WorkerResult(
                task=search_plan,
                output="\n".join(search_results),
            )
        )
        report = await self._write_report(query, search_results)
        report_to_show = "\n".join([report.markdown_report, "\n", "\n".join(report.follow_up_questions)])
        yield OrchestraStreamEvent(
            name="report",
            item=AnalysisResult(
                output=report_to_show,
            )
        )
    
    async def run(self, query: str) -> None:
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            search_plan = await self._plan_searches(query)
            search_results = await self._perform_searches(search_plan)
            report = await self._write_report(query, search_results)

            final_report = f"Report summary\n\n{report.short_summary}

        print("\n\n=====REPORT=====\n\n")
        print(f"Report: {report.markdown_report}")
        print("\n\n=====FOLLOW UP QUESTIONS=====\n\n")
        follow_up_questions = "\n".join(report.follow_up_questions)
        print(f"Follow up questions: {follow_up_questions}")

    async def _plan_searches(self, query: str) -> WebSearchPlan:
        result = await planner_agent.run(
            f"Query: {query}",
        )
        return result.get_run_result().final_output_as(WebSearchPlan)
        
    async def _plan_searches_streamed(self, query: str) -> WebSearchPlan:
        result = await planner_agent.run_streamed(
            f"Query: {query}",
        )
        return result

    async def _perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        with custom_span("Search the web"):
            num_completed = 0
            tasks = [asyncio.create_task(self._search(item)) for item in search_plan.searches]
            results = []
            for task in asyncio.as_completed(tasks):
                result = await task
                if result is not None:
                    results.append(result)
                num_completed += 1
            # results = await asyncio.gather(*tasks)
            return results

    async def _search(self, item: WebSearchItem) -> str | None:
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await search_agent.run(
                input,
            )
            return str(result.final_output)
        except Exception:  # pylint: disable=broad-except
            return None

    async def _write_report(self, query: str, search_results: list[str]) -> ReportData:
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await writer_agent.run(
            input,
        )
        return result.get_run_result().final_output_as(ReportData)


async def main() -> None:
    async with planner_agent, search_agent, writer_agent:  # agent context control
        query = input("What would you like to research? ")
        research_manager = ResearchManager()
        webui = WebUIChatbot()


if __name__ == "__main__":
    asyncio.run(main())
