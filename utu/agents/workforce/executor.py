"""
- [ ] error tracing
"""

from ...config import AgentConfig
from ...utils import FileUtils, get_logger
from ..llm_agent import LLMAgent
from ..simple_agent import SimpleAgent
from .data import Subtask, WorkspaceTaskRecorder

logger = get_logger(__name__)

PROMPTS = FileUtils.load_prompts("agents/workforce/executor.yaml")


class ExecutorAgent:
    """Executor agent that executes tasks assigned by the planner.

    - TODO: self-reflection
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.executor_agent = SimpleAgent(config=config)
        self.llm = LLMAgent(config.model)  # summary llm, use the same model as executor_agent
        # self._reflection_history = []
        executor_config = config.workforce_executor_config
        self.max_tries = executor_config.get("max_tries", 1)
        self.return_summary = executor_config.get("return_summary", False)

    async def execute_task(
        self,
        recorder: WorkspaceTaskRecorder,
        task: Subtask,
    ) -> None:
        """Execute the task and check the result."""
        task.task_status = "in progress"

        tries = 1
        final_result = None
        executor_res = None
        while tries <= self.max_tries:
            try:
                # * 1. Task execution
                user_prompt = PROMPTS["TASK_EXECUTE_USER_PROMPT"].format(
                    overall_task=recorder.overall_task,
                    overall_plan=recorder.formatted_task_plan,
                    task_name=task.task_name,
                    task_description=task.task_description,
                )
                executor_res = await self.executor_agent.run(user_prompt)
                final_result = executor_res.final_output

                break
                # TODO: task check
                # # * 2. Task check
                # task_check_prompt = PROMPTS["TASK_CHECK_PROMPT"].format(
                #     task_name=task_name,
                #     task_description=task_description,
                # )

                # parsed_response_content = self._parse_task_check_result(response_content)
                # if parsed_response_content is True:
                #     logger.info(f"Task '{task_name}' completed successfully.")
                #     break
                # else:
                #     logger.warning(f"Task '{task_name}' not completed. Retrying... (Attempt {tries}/{max_tries})")
                #     reflection_prompt = TASK_REFLECTION_PROMPT.format()

            except Exception as e:
                logger.error(f"Error executing task `{task.task_name}` on attempt {tries}: {str(e)}")
                tries += 1
                if tries > self.max_tries:
                    final_result = f"Task execution failed: {str(e)}"
                    break

        if executor_res:
            recorder.add_run_result(executor_res.get_run_result(), "executor")  # add executor trajectory
        task.task_result = final_result
        task.task_status = "completed"

        # TODO: use the history (res.get_run_result().to_input_list()) during summary?
        if self.return_summary:
            summary_prompt = PROMPTS["TASK_SUMMARY_USER_PROMPT"].format(
                task_name=task.task_name, task_description=task.task_description
            )
            summary_response = await self.llm.run(summary_prompt)
            recorder.add_run_result(summary_response.get_run_result(), "executor")  # add executor trajectory
            task.task_result_detailed, task.task_result = summary_response.final_output, summary_response.final_output
            logger.info(f"Task result summarized: {task.task_result_detailed} -> {task.task_result}")
