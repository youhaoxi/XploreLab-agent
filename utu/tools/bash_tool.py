""" 
https://github.com/pexpect/pexpect
@ii-agent/src/ii_agent/tools/bash_tool.py
"""

import re
import logging
from typing import Callable

import pexpect

from .base import AsyncBaseToolkit
from ..config import ToolkitConfig

logger = logging.getLogger("utu")


def start_persistent_shell(timeout: int) -> tuple[pexpect.spawn, str]:
    # Start a new Bash shell
    child = pexpect.spawn("/bin/bash", encoding="utf-8", echo=False, timeout=timeout)
    # Set a known, unique prompt
    # We use a random string that is unlikely to appear otherwise
    # so we can detect the prompt reliably.
    custom_prompt = "PEXPECT_PROMPT>> "
    child.sendline("stty -onlcr")
    child.sendline("unset PROMPT_COMMAND")
    child.sendline(f"PS1='{custom_prompt}'")
    # Force an initial read until the newly set prompt shows up
    child.expect(custom_prompt)
    return child, custom_prompt

def run_command(child: pexpect.spawn, custom_prompt: str, cmd: str) -> str:
    # Send the command
    child.sendline(cmd)
    # Wait until we see the prompt again
    child.expect(custom_prompt)
    # Output is everything printed before the prompt minus the command itself
    # pexpect puts the matched prompt in child.after and everything before it in child.before.

    raw_output = child.before.strip()
    ansi_escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
    clean_output = ansi_escape.sub("", raw_output)

    if clean_output.startswith("\r"):
        clean_output = clean_output[1:]

    return clean_output


class BashTool(AsyncBaseToolkit):
    def __init__(self, config: ToolkitConfig = None, activated_tools: list[str] = None) -> None:
        super().__init__(config, activated_tools)
        self.workspace_root = self.config.config.get("workspace_root", "/tmp/")
        # self.require_confirmation = self.config.config.get("require_confirmation", False)
        # self.command_filters = self.config.config.get("command_filters", [])
        self.timeout = self.config.config.get("timeout", 60)
        self.banned_command_strs = [
            "git init",
            "git commit",
            "git add",
        ]

        self.child, self.custom_prompt = start_persistent_shell(timeout=self.timeout)
        if self.workspace_root:
            run_command(self.child, self.custom_prompt, f"cd {self.workspace_root}")

    async def run_bash(self, command: str) -> str:
        """Execute a bash command and return its output.

        Args:
            tool_input: Dictionary containing the command to execute

        Returns:
            ToolImplOutput containing the command output
        """
        # 1) filter: change command before execution. E.g. used in SSH or Docker.
        # original_command = command
        # command = self.apply_filters(original_command)
        # if command != original_command:
        #     logger.info(f"Command filtered: {original_command} -> {command}")

        # 2) banned command check
        for banned_str in self.banned_command_strs:
            if banned_str in command:
                return f"Command not executed due to banned string in command: {banned_str} found in {command}."
        
        # if self.require_confirmation:
        #     ...

        # confirm no bad stuff happened
        try:
            echo_result = run_command(self.child, self.custom_prompt, "echo hello")
            assert echo_result.strip() == "hello"
        except Exception:
            self.child, self.custom_prompt = start_persistent_shell(self.timeout)

        # 3) Execute the command and capture output
        try:
            result = run_command(self.child, self.custom_prompt, command)
            return str({
                "command output": result,
            })
        except Exception as e:
            return str({
                "error": str(e),
            })
        # TODO: add workspace tree in output


    async def get_tools_map(self) -> dict[str, Callable]:
        return {
            "bash": self.run_bash,
        }