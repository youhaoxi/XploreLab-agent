import re


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
    def extract_code_python(self, s: str) -> str:
        """Extract the first python code block from the given string."""
        code_blocks = self.extract_code_blocks(s)
        if not code_blocks:
            return s  # fallback
        for language, code in code_blocks:
            if language.lower() in ["python", "py"]:
                return code
        return code_blocks[0][1]  # fallback

    @classmethod
    def extract_code_json(self, s: str) -> str:
        """Extract the first json code block from the given string."""
        code_blocks = self.extract_code_blocks(s)
        if not code_blocks:
            return s  # fallback
        for language, code in code_blocks:
            if language.lower() in ["json"]:
                return code
        return code_blocks[0][1]  # fallback
