from collections.abc import Callable

from openai.types.audio import TranscriptionVerbose

from ..config import ToolkitConfig
from ..utils import DIR_ROOT, FileUtils, SimplifiedAsyncOpenAI, async_file_cache, get_logger
from .base import TOOL_PROMPTS, AsyncBaseToolkit

logger = get_logger(__name__)


class AudioToolkit(AsyncBaseToolkit):
    def __init__(self, config: ToolkitConfig = None) -> None:
        super().__init__(config)
        self.client = SimplifiedAsyncOpenAI(**config.config["audio_model"])
        self.llm = SimplifiedAsyncOpenAI(**config.config_llm.model_provider.model_dump())
        self.md5_to_path = {}

    @async_file_cache(expire_time=None)
    async def transcribe(self, md5: str) -> dict:
        # model: gpt-4o-transcribe, gpt-4o-mini-transcribe, and whisper-1
        fn = self.md5_to_path[md5]
        transcript: TranscriptionVerbose = await self.client.audio.transcriptions.create(
            model=self.config.config["audio_model"]["model"],
            file=open(fn, "rb"),
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )
        return transcript.model_dump()

    def handle_path(self, path: str) -> str:
        md5 = FileUtils.get_file_md5(path)
        if FileUtils.is_web_url(path):
            # download audio to data/_audio, with md5
            fn = DIR_ROOT / "data" / "_audio" / f"{md5}{FileUtils.get_file_ext(path)}"
            fn.parent.mkdir(parents=True, exist_ok=True)
            if not fn.exists():
                path = FileUtils.download_file(path, fn)
                logger.info(f"Downloaded audio file to {path}")
            path = fn
        self.md5_to_path[md5] = path  # record md5 to map
        return md5

    async def audio_qa(self, audio_path: str, question: str) -> str:
        """Asks a question about the audio and gets an answer.

        Args:
            audio_path (str): The path or URL to the audio file.
            question (str): The question to ask about the audio.
        """
        logger.debug(f"Processing audio file `{audio_path}` with question `{question}`.")
        md5 = self.handle_path(audio_path)
        res = await self.transcribe(md5)

        messages = [
            {"role": "system", "content": "You are a helpful assistant specializing in audio analysis."},
            {
                "role": "user",
                "content": TOOL_PROMPTS["audio_qa"].format(
                    question=question, file=audio_path, duration=res["duration"], transcription=res["text"]
                ),
            },
        ]
        output = await self.llm.query_one(messages=messages, **self.config.config_llm.model_params.model_dump())
        return output

    async def get_tools_map(self) -> dict[str, Callable]:
        return {
            "audio_qa": self.audio_qa,
        }
