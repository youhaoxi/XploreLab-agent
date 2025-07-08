import abc
import json
import logging
import pathlib
from typing import Literal

from sqlmodel import SQLModel, create_engine, Session, select

from ...config import EvalConfig
from ..data_processer import BUILTIN_BENCHMARKS, DATA_PROCESSER_FACTORY, BaseProcesser
from . import EvaluationSample as Datapoint

logger = logging.getLogger(__name__)


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


class Dataset(BaseDataManager):
    _source_to_processer: dict[str, BaseProcesser]

    def load(self) -> list[Datapoint]:
        data_path = self._get_data_path()
        samples = []
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line.strip())
                assert "source" in data, f"Missing source in data: {data}"
                # assert data["source"].lower() in DATA_PROCESSER_FACTORY._registry, f"Unknown source: {data['source']}"
                processer = DATA_PROCESSER_FACTORY.get(data["source"], self.config)
                sample = processer.process_one(data)
                sample.update(exp_id=self.config.exp_id)  # set exp_id!
                samples.append(sample)
        self.data = samples
        return samples

    def _get_data_path(self) -> pathlib.Path:
        if self.config.type == "single" and self.config.dataset in BUILTIN_BENCHMARKS:
            data_path = pathlib.Path(BUILTIN_BENCHMARKS[self.config.dataset]["data_path"])
        else:
            data_path = pathlib.Path(self.config.dataset)
        assert data_path.exists(), f"Data file {data_path} does not exist."
        assert str(data_path).endswith(".jsonl"), f"Only support .jsonl files, but got {data_path}."
        return data_path

    def get_samples(self, stage: Literal["init", "rollout", "judged"] = None) -> list[Datapoint]:
        return [d for d in self.data if d.stage == stage]

    def save(self, ofn: str) -> None:
        with open(ofn, 'w', encoding='utf-8') as f:
            for sample in self.data:
                f.write(json.dumps(sample.as_dict()) + '\n')


class DBDataset(Dataset):
    def __init__(self, config: EvalConfig) -> None:
        self.config = config
        self.engine = create_engine("sqlite:///evaluation_samples.db")
        SQLModel.metadata.create_all(self.engine)

    def load(self) -> list[Datapoint]:
        if self._check_exp_id():
            logger.warning(f"exp_id {self.config.exp_id} already exists in db")
            return self.get_samples()
        self.data = super().load()
        self.save(self.data)  # save to db
        return self.data

    def get_samples(self, stage: Literal["init", "rollout", "judged"] = None) -> list[Datapoint]:
        """Get samples from exp_id with specified stage."""
        with Session(self.engine) as session:
            samples = session.exec(
                select(Datapoint).where(
                    Datapoint.exp_id == self.config.exp_id,
                    Datapoint.stage == stage if stage else True
                )
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
