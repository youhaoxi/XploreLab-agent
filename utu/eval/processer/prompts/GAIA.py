SYSTEM_PROMPT = """
You are a helpful assistant.
""".strip()

AUGMENTED_TEMPLATE = """
It is paramount that you complete this task and provide a correct answer.
Give it all you can: I know for a fact that you have access to all the relevant tools to solve it. Failure or 'I cannot answer' will not be tolerated, success will be rewarded.
Here is the task:
{question}
""".strip()

JUDGE_TEMPLATE = None
