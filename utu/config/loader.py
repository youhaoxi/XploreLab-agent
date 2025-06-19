from typing import TypeVar, Type

from pydantic import BaseModel
from dotenv import load_dotenv

from omegaconf import OmegaConf

load_dotenv()
TConfig = TypeVar("TConfig", bound=BaseModel)


class ModelConfig(BaseModel):
    api_key: str
    base_url: str
    model: str

class Config(BaseModel):
    model: ModelConfig

def load_config(config_path: str, config_type: Type[TConfig] = Config) -> TConfig:
    config = OmegaConf.load(config_path)
    config = OmegaConf.to_container(config, resolve=True)
    structed_config = config_type(**config)
    return structed_config
