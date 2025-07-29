import abc
import json
import pathlib
from typing import Literal

from sqlmodel import SQLModel, create_engine, Session, select

from ...config import EvalConfig
from ...db import EvaluationSample as Datapoint
from ..processer import BUILTIN_BENCHMARKS
from ...utils import get_logger

logger = get_logger(__name__)


class BaseDataManager(abc.ABC):
    data: list[Datapoint]

    def __init__(self, config: EvalConfig) -> None:
        self.config = config

    @abc.abstractmethod
    def load(self) -> list[Datapoint]:
        """Load the dataset."""
        raise NotImplementedError

    @abc.abstractmethod
    def save(self, **kwargs) -> None:
        """Save the dataset."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_samples(self, stage: Literal["init", "rollout", "judged"] = None) -> list[Datapoint]:
        """Get samples of specified stage from the dataset."""
        raise NotImplementedError


class DataManager(BaseDataManager):
    def load(self) -> list[Datapoint]:
        """ Load raw data from the specified dataset. """
        data_path = self._get_data_path()
        samples = []
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line.strip())
                # assert "source" in data, f"Missing source in data: {data}"
                # assert data["source"].lower() in DATA_PROCESSER_FACTORY._registry, f"Unknown source: {data['source']}"
                sample = Datapoint(
                    source=data.get("source", self.config.data.dataset),
                    raw_question=data.get(self.config.data.question_field, ""),
                    level=data.get("level", 0),  # if applicable
                    correct_answer=data.get(self.config.data.gt_field, ""),
                    file_name=data.get("file name", ""),  # for GAIA
                    exp_id=self.config.exp_id,
                )
                samples.append(sample)
        self.data = samples
        return samples

    def _get_data_path(self) -> pathlib.Path:
        if self.config.data.type == "single" and self.config.data.dataset in BUILTIN_BENCHMARKS:
            data_path = pathlib.Path(BUILTIN_BENCHMARKS[self.config.data.dataset]["data_path"])
        else:
            data_path = pathlib.Path(self.config.data.dataset)
        assert data_path.exists(), f"Data file {data_path} does not exist."
        assert str(data_path).endswith(".jsonl"), f"Only support .jsonl files, but got {data_path}."
        return data_path

    def get_samples(self, stage: Literal["init", "rollout", "judged"] = None) -> list[Datapoint]:
        return [d for d in self.data if d.stage == stage]

    def save(self, ofn: str) -> None:
        with open(ofn, 'w', encoding='utf-8') as f:
            for sample in self.data:
                f.write(json.dumps(sample.as_dict()) + '\n')


class DBDataManager(DataManager):
    def __init__(self, config: EvalConfig) -> None:
        self.config = config
        self.engine = create_engine(self.config.db_url, pool_size=30, max_overflow=50, pool_timeout=30)
        SQLModel.metadata.create_all(self.engine)

    def load(self) -> list[Datapoint]:
        if self._check_exp_id():
            logger.warning(f"exp_id {self.config.exp_id} already exists in db")
            return self.get_samples()
        self.data = super().load()
        self.save(self.data)  # save to db
        return self.data

    def get_samples(self, stage: Literal["init", "rollout", "judged"] = None, limit: int = None) -> list[Datapoint]:
        """Get samples from exp_id with specified stage."""
        with Session(self.engine) as session:
            samples = session.exec(
                select(Datapoint).where(
                    Datapoint.exp_id == self.config.exp_id,
                    Datapoint.stage == stage if stage else True,
                ).limit(limit)
            ).all()
            return samples

    def save(self, samples: list[Datapoint]|Datapoint) -> None:
        """Update or add sample(s) to db."""
        if isinstance(samples, list):
            with Session(self.engine) as session:
                session.add_all(samples)
                session.commit()
        else:
            with Session(self.engine) as session:
                session.add(samples)
                session.commit()

    def delete_samples(self, samples: list[Datapoint]|Datapoint) -> None:
        """Delete sample(s) from db."""
        if isinstance(samples, list):
            with Session(self.engine) as session:
                for sample in samples:
                    session.delete(sample)
                session.commit()
        else:
            with Session(self.engine) as session:
                session.delete(samples)
                session.commit()

    def _check_exp_id(self) -> bool:
        # check if any record has the same exp_id
        with Session(self.engine) as session:
            has_exp_id = session.exec(
                select(Datapoint).where(
                    Datapoint.exp_id == self.config.exp_id
                )
            ).first()
        return has_exp_id is not None
