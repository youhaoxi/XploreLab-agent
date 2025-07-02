from dataclasses import dataclass


@dataclass
class EvaluationSample:
    """
    A data class to represent a single evaluation sample.
    """
    source: str  # source benchmark
    raw_question: str
    level: int  # hardness level of the question, if applicable
    augmented_question: str
    correct_answer: str
    file_name: str  # for GAIA
    response: str
    # below for judgement
    extracted_final_answer: str
    judged_response: str
    reasoning: str
    correct: bool
    confidence: int
    # tracing
    time_cost: float = None  # time cost in seconds
    trajectory: list = None  # the agent's reasoning process, a list of messages

    def __init__(self, **kwargs):
        """
        Initialize the EvaluationSample with keyword arguments.
        """
        self.source = kwargs.get('source', '')
        self.raw_question = kwargs.get('raw_question', '')
        self.level = kwargs.get('level', 0)
        self.augmented_question = kwargs.get('augmented_question', '')
        self.correct_answer = kwargs.get('correct_answer', '')
        self.file_name = kwargs.get('file_name', '')
        self.response = kwargs.get('response', None)
        self.extracted_final_answer = kwargs.get('extracted_final_answer', None)
        self.judged_response = kwargs.get('judged_response', None)
        self.reasoning = kwargs.get('reasoning', None)
        self.correct = kwargs.get('correct', None)
        self.confidence = kwargs.get('confidence', None)
        self.trajectory = kwargs.get('trajectory', None)

    def update(self, **kwargs):
        """
        Update the evaluation sample with the given keyword arguments.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get(self, key, default=None):
        """
        Get the value of the specified key, or return default if not found.
        """
        return getattr(self, key, default)
    
    @classmethod
    def from_dict(cls, data: dict):
        """
        Create an EvaluationSample from a dictionary.
        """
        return cls(**data)
    
    def as_dict(self) -> dict:
        # only contain fields that are not None
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class EvaluationResult:
    """
    A data class to represent the result of an evaluation.
    """
    benchmark: str
    metrics: dict

    def update(self, **kwargs):
        """
        Update the evaluation result with the given keyword arguments.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def as_dict(self):
        """
        Convert the evaluation result to a dictionary.
        """
        return {
            "benchmark": self.benchmark,
            "metrics": self.metrics
        }
