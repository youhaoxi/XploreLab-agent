import re
import json
from typing import Dict, List, Optional, Union
from dataclasses import dataclass


@dataclass
class PlannerTask:
    """表示规划器中的单个任务"""
    agent_name: str
    task: str
    completed: bool


@dataclass
class NextStep:
    """表示下一步要执行的任务"""
    agent_name: str
    task: str


@dataclass
class PlannerOutput:
    """表示规划器的完整输出"""
    analysis: str
    plan: List[PlannerTask]
    next_step: Optional[NextStep] = None
    task_finished: bool = False


class PlannerOutputParser:
    """解析规划器输出内容的解析器"""
    
    def __init__(self):
        self.analysis_pattern = r'<analysis>(.*?)</analysis>'
        self.plan_pattern = r'<plan>\s*\[(.*?)\]\s*</plan>'
        self.next_step_pattern = r'<next_step>\s*<agent>\s*(.*?)\s*</agent>\s*<task>\s*(.*?)\s*</task>\s*</next_step>'
        self.task_finished_pattern = r'<task_finished>\s*</task_finished>'
    
    def parse(self, output_text: str) -> PlannerOutput:
        """
        解析规划器的输出文本
        
        Args:
            output_text: 规划器的原始输出文本
            
        Returns:
            PlannerOutput: 解析后的结构化输出
        """
        # 提取analysis部分
        analysis = self._extract_analysis(output_text)
        
        # 提取plan部分
        plan = self._extract_plan(output_text)
        
        # 检查是否任务完成
        task_finished = self._check_task_finished(output_text)
        
        # 提取next_step部分（如果不是任务完成状态）
        next_step = None if task_finished else self._extract_next_step(output_text)
        
        return PlannerOutput(
            analysis=analysis,
            plan=plan,
            next_step=next_step,
            task_finished=task_finished
        )
    
    def _extract_analysis(self, text: str) -> str:
        """提取analysis部分的内容"""
        match = re.search(self.analysis_pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_plan(self, text: str) -> List[PlannerTask]:
        """提取plan部分的任务列表"""
        match = re.search(self.plan_pattern, text, re.DOTALL)
        if not match:
            return []
        
        plan_content = match.group(1).strip()
        tasks = []
        
        # 使用正则表达式匹配每个任务的字典格式
        task_pattern = r'\{"agent_name":\s*"([^"]+)",\s*"task":\s*"([^"]+)",\s*"completed":\s*(true|false)\s*\}'
        task_matches = re.findall(task_pattern, plan_content, re.IGNORECASE)
        
        for agent_name, task_desc, completed_str in task_matches:
            completed = completed_str.lower() == 'true'
            tasks.append(PlannerTask(
                agent_name=agent_name,
                task=task_desc,
                completed=completed
            ))
        
        return tasks
    
    def _extract_next_step(self, text: str) -> Optional[NextStep]:
        """提取next_step部分的内容"""
        match = re.search(self.next_step_pattern, text, re.DOTALL)
        if match:
            agent_name = match.group(1).strip()
            task = match.group(2).strip()
            return NextStep(agent_name=agent_name, task=task)
        return None
    
    def _check_task_finished(self, text: str) -> bool:
        """检查是否包含task_finished标签"""
        return bool(re.search(self.task_finished_pattern, text))
    
    def to_dict(self, parsed_output: PlannerOutput) -> Dict:
        """将解析结果转换为字典格式"""
        result = {
            "analysis": parsed_output.analysis,
            "plan": [
                {
                    "agent_name": task.agent_name,
                    "task": task.task,
                    "completed": task.completed
                }
                for task in parsed_output.plan
            ],
            "task_finished": parsed_output.task_finished
        }
        
        if parsed_output.next_step:
            result["next_step"] = {
                "agent_name": parsed_output.next_step.agent_name,
                "task": parsed_output.next_step.task
            }
        
        return result
    
    def to_json(self, parsed_output: PlannerOutput, indent: int = 2) -> str:
        """将解析结果转换为JSON格式"""
        return json.dumps(self.to_dict(parsed_output), ensure_ascii=False, indent=indent)
