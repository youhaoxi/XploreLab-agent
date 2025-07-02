
import logging
from typing import List, Optional, Literal
from datetime import datetime

from sqlmodel import SQLModel, Field, create_engine, Session, select

from ...config import EvalConfig
from ..data import EvaluationSample
from .file_data_manager import FileDataManager

logger = logging.getLogger("utu")


class EvaluationSampleSQL(SQLModel, EvaluationSample, table=True):
    __tablename__ = 'evaluation_samples'
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class DBDataManager(FileDataManager):
    def __init__(self, config: EvalConfig):
        super().__init__(config)
        self.engine = create_engine("sqlite:///evaluation_samples.db")
    
    async def init(self) -> list[EvaluationSampleSQL]:
        SQLModel.metadata.create_all(self.engine)

        # check if exp_id exists
        if self._check_exp_id():
            logger.warning(f"exp_id {self.config.exp_id} already exists in db")
        else:
            # if not, load and save samples to db -> state: init
            _samples = await self.load_dataset()
            for sample in _samples:
                sample.exp_id = self.config.exp_id  # setup exp_id!
            samples_sql = [EvaluationSampleSQL(**sample.as_dict()) for sample in _samples]
            await self.update_samples(samples_sql)
        return await self.get_samples()

    def _check_exp_id(self) -> bool:
        # check if any record has the same exp_id
        with Session(self.engine) as session:
            has_exp_id = session.exec(
                select(EvaluationSampleSQL).where(
                    EvaluationSampleSQL.exp_id == self.config.exp_id
                )
            ).first()
        return has_exp_id is not None

    async def get_samples(self, stage: Literal["init", "rollout", "judgement"] = None) -> list[EvaluationSampleSQL]:
        """Get samples from exp_id with specified stage."""
        with Session(self.engine) as session:
            samples = session.exec(
                select(EvaluationSampleSQL).where(
                    EvaluationSampleSQL.exp_id == self.config.exp_id,
                    EvaluationSampleSQL.stage == stage if stage else True
                )
            ).all()
            return samples

    async def update_samples(self, samples: list[EvaluationSampleSQL]|EvaluationSampleSQL) -> None:
        """Update or add sample(s) to db."""
        if isinstance(samples, list):
            with Session(self.engine) as session:
                session.add_all(samples)
                session.commit()
        else:
            with Session(self.engine) as session:
                session.add(samples)
                session.commit()

    async def delete_samples(self, samples: list[EvaluationSampleSQL]|EvaluationSampleSQL) -> None:
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
