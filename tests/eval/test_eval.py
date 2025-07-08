import json
from agents.models.chatcmpl_converter import Converter

from utu.eval.data import EvaluationSample
from utu.eval.evaluation import MixedEval
from utu.agents import build_agent
from utu.config import EvalConfig


async def test_agent_rollout(config: EvalConfig, data: list[EvaluationSample], evaluator: MixedEval):
    # build agent
    sample = data[0]
    source = sample.source
    instructions = evaluator.get_instructions().get(source)
    agent = build_agent(config=config.agent, instructions=instructions)
    await agent.build()
    
    # rollout
    result = await agent.chat(sample.augmented_question)
    trajectory = Converter.items_to_messages(result.to_input_list())
    print(json.dumps(trajectory, ensure_ascii=False, indent=2))