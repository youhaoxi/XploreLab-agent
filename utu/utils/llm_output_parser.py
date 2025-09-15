import json
import re

LANGUAGE_TO_CANDS = {
    "python": ["py", "python"],
    "json": ["json"],
    "javascript": ["js", "javascript"],
    "yaml": ["yaml", "yml"],
}


class LLMOutputParser:
    @classmethod
    def extract_code_blocks(self, s: str) -> list[tuple[str, str]]:
        """Parse all code blocks (language, code) from the given string."""
        pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
        code_blocks = []
        for match in pattern.finditer(s):
            language = match.group(1).strip()
            code = match.group(2).strip()
            code_blocks.append((language, code))
        return code_blocks

    @classmethod
    def extract_code_block_with_language(self, s: str, language: str) -> str:
        code_blocks = self.extract_code_blocks(s)
        if not code_blocks:
            return s  # fallback
        for lang, code in code_blocks:
            if lang.lower() in LANGUAGE_TO_CANDS[language]:
                return code
        return code_blocks[0][1]  # fallback

    @classmethod
    def extract_code_python(self, s: str) -> str:
        """Extract the first code block with the given language from the given string."""
        return self.extract_code_block_with_language(s, "python")

    @classmethod
    def extract_code_json(self, s: str, try_parse: bool = True) -> str | dict:
        """Extract the first json code block from the given string."""
        code = self.extract_code_block_with_language(s, "json")
        if try_parse:
            try:
                return json.loads(code)
            except json.JSONDecodeError:
                return code
        return code
