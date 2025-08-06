import abc
import datetime

from agents import Tool


class Env(abc.ABC):
    @staticmethod
    def get_time() -> str:
        return datetime.datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")

    @abc.abstractmethod
    def get_sp_prefix(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_state(self) -> str:
        raise NotImplementedError


    @abc.abstractmethod
    async def get_tools(self) -> list[Tool]:
        raise NotImplementedError

    async def build(self):
        pass

    async def cleanup(self):
        pass

    async def __aenter__(self):
        await self.build()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()


class BaseEnv(Env):
    def get_sp_prefix(self) -> str:
        return ""

    def get_state(self) -> str:
        return ""

    async def get_tools(self) -> list[Tool]:
        return []
