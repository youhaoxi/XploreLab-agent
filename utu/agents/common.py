from agents import RunResult

from ..utils import AgentsUtils


class TaskRecorder:
    def __init__(self, task: str, trace_id: str):
        self.task = task
        self.trace_id = trace_id

        self.final_output: str = ""
        self.trajectories: list = []

        self.raw_run_results: list[RunResult] = []

    def add_run_result(self, run_result: RunResult):
        self.raw_run_results.append(run_result)
        self.trajectories.append(AgentsUtils.get_trajectory_from_agent_result(run_result))

    def get_run_result(self) -> RunResult:
        return self.raw_run_results[-1]

    def set_final_output(self, final_output: str):
        self.final_output = final_output
