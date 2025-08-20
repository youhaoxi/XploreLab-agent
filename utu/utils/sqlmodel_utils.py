from sqlmodel import Session, create_engine, text

from .env import EnvUtils
from .log import get_logger

logger = get_logger(__name__)


class SQLModelUtils:
    _engine = None  # singleton

    @classmethod
    def get_engine(cls):
        if cls._engine is None:
            cls._engine = create_engine(
                EnvUtils.get_env("DB_URL"), pool_size=300, max_overflow=500, pool_timeout=30, pool_pre_ping=True
            )
        return cls._engine

    @staticmethod
    def create_session():
        return Session(SQLModelUtils.get_engine())

    @staticmethod
    def check_db_available():
        if not EnvUtils.get_env("DB_URL"):
            # logger.error("DB_URL is not set")
            return False
        try:
            engine = SQLModelUtils.get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
