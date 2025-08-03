import pathlib
from datetime import datetime
from typing import Literal

from jinja2 import Environment, FileSystemLoader

from ..agents.utils import Base, NextTaskResult, Task
from ...config import AgentConfig
from ...utils import SimplifiedAsyncOpenAI
from .session_manager import SessionManager
from .output_parser import PlannerOutputParser


PROMPT_DIR = pathlib.Path(__file__).parent / "config"


class PlannerAgent(Base):
    def __init__(self, config: AgentConfig=None):
        super().__init__(config)
        with open(PROMPT_DIR / "planner_agent.SP.md", "r", encoding="utf-8") as f:
            self.sp_prompt = f.read()
        self.jinja_env = Environment(loader=FileSystemLoader(PROMPT_DIR))
        self.planning_mode_template = self.jinja_env.get_template("planner_agent.UP.planning_mode.jinja")
        self.update_planning_mode_template = self.jinja_env.get_template("planner_agent.UP.update_planning_mode.jinja")
        self.llm = SimplifiedAsyncOpenAI()
        self.output_parser = PlannerOutputParser()

    async def get_next_task(self, query=None, prev_task=None, prev_subtask_result=None, trace_id=None) -> NextTaskResult:
        """ get next task to execute """
        if not prev_subtask_result:
            result = await self.create_plan(query, session_id=trace_id)
            return NextTaskResult(task=Task(**result["next_step"]), todo=result["plan"])
        else:
            result = await self.update_plan(prev_task, prev_subtask_result, session_id=trace_id)
            return NextTaskResult(task=Task(**result["next_step"]), todo=result["plan"])

    async def execute_planning(self, mode: Literal["planning", "update_planning"], question: str, background_info: str = "",
                        previous_plan: str = "", task: str = "", task_results: str = "", 
                        session_id: str = None) -> dict:
        messages = [{"role": "system", "content": self.sp_prompt}]
        if mode == "planning":
            up = self.planning_mode_template.render(
                question=question,
                background_info=background_info,
            )
            messages.append({"role": "user", "content": up})
        elif mode == "update_planning":
            up = self.update_planning_mode_template.render(
                question=question,
                background_info=background_info,
                previous_plan=previous_plan,
                task=task,
                task_results=task_results,
            )
            messages.append({"role": "user", "content": up})
        response = await self.llm.query_one(messages=messages)
        result = self.output_parser.parse(response)
        return self.output_parser.to_dict(result) # {next_step, plan, ...}
    
    async def create_plan(self, question: str, background_info: str = "", session_id: str = None) -> dict:
        if SessionManager.session_exists(session_id):
            raise ValueError("Session already exists")
        SessionManager.create_new_session(session_id)
        session_data = SessionManager.load_session(session_id)
        result = await self.execute_planning("planning", question, background_info, session_id=session_id)
        session_record = {
            "timestamp": datetime.now().isoformat(),
            "mode": "planning",
            "request": {
                "question": question,
                "background_info": background_info
            },
            "response": result
        }
        session_data['history'].append(session_record)
        SessionManager.save_session(session_id, session_data)
        return result

    async def update_plan(self, task: str, task_results: str, session_id: str = None):
        question, background_info = SessionManager.get_session_question_and_background(session_id)
        previous_plan = SessionManager.get_latest_plan(session_id)
        result = await self.execute_planning("update_planning", question, background_info, previous_plan, task, task_results, session_id=session_id)
        session_data = SessionManager.load_session(session_id)
        session_record = {
            "timestamp": datetime.now().isoformat(),
            "mode": "update_planning",
            "request": {
                "question": question,
                "background_info": background_info,
                "previous_plan": previous_plan,
                "task": task,
                "task_results": task_results
            },
            "response": result
        }
        session_data['history'].append(session_record)
        SessionManager.save_session(session_id, session_data)
        return result
