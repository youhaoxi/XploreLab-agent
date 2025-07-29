""" 
by @ianxxu

--- https://www.anthropic.com/engineering/swe-bench-sonnet ---
Custom editing tool for viewing, creating and editing files\n
* State is persistent across command calls and discussions with the user\n
* If `path` is a file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep\n
* The `create` command cannot be used if the specified `path` already exists as a file\n
* If a `command` generates a long output, it will be truncated and marked with `<response clipped>` \n
* The `undo_edit` command will revert the last edit made to the file at `path`\n
\n
Notes for using the `str_replace` command:\n
* The `old_str` parameter should match EXACTLY one or more consecutive lines from the original file. Be mindful of whitespaces!\n
* If the `old_str` parameter is not unique in the file, the replacement will not be performed. Make sure to include enough context in `old_str` to make it unique\n
* The `new_str` parameter should contain the edited lines that should replace the `old_str`",

   "input_schema": {
       "type": "object",
       "properties": {
           "command": {
               "type": "string",
               "enum": ["view", "create", "str_replace", "insert", "undo_edit"],
               "description": "The commands to run. Allowed options are: `view`, `create`, `str_replace`, `insert`, `undo_edit`."
           },
           "file_text": {
               "description": "Required parameter of `create` command, with the content of the file to be created.",
               "type": "string"
           },
           "insert_line": {
               "description": "Required parameter of `insert` command. The `new_str` will be inserted AFTER the line `insert_line` of `path`.",
               "type": "integer"
           },
           "new_str": {
               "description": "Required parameter of `str_replace` command containing the new string. Required parameter of `insert` command containing the string to insert.",
               "type": "string"
           },
           "old_str": {
               "description": "Required parameter of `str_replace` command containing the string in `path` to replace.",
               "type": "string"
           },
           "path": {
               "description": "Absolute path to file or directory, e.g. `/repo/file.py` or `/repo`.",
               "type": "string"
           },
           "view_range": {
               "description": "Optional parameter of `view` command when `path` points to a file. If none is given, the full file is shown. If provided, the file will be shown in the indicated line number range, e.g. [11, 12] will show lines 11 and 12. Indexing at 1 to start. Setting `[start_line, -1]` shows all lines from `start_line` to the end of the file.",
               "items": {
                   "type": "integer"
               },
               "type": "array"
           }
       },
       "required": ["command", "path"]
   }
"""

import logging
import shutil
import re
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

from .base import AsyncBaseToolkit
from ..config import ToolkitConfig

logger = logging.getLogger(__name__)


class FileEditToolkit(AsyncBaseToolkit):
    def __init__(self, config: ToolkitConfig = None) -> None:
        super().__init__(config)
        self.work_dir = Path(self.config.config.get("work_dir", "./")).resolve()
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.default_encoding = self.config.config.get("default_encoding", "utf-8")
        self.backup_enabled = self.config.config.get("backup_enabled", True)
        logger.info(
            f"FileEditToolkit initialized with output directory"
            f": {self.work_dir}, encoding: {self.default_encoding}"
        )

    def _sanitize_filename(self, filename: str) -> str:
        r"""Sanitize a filename by replacing any character that is not
        alphanumeric, a dot (.), hyphen (-), or underscore (_) with an
        underscore (_).

        Args:
            filename (str): The original filename which may contain spaces or
                special characters.

        Returns:
            str: The sanitized filename with disallowed characters replaced by
                underscores.
        """
        safe = re.sub(r'[^\w\-.]', '_', filename)
        return safe

    def _resolve_filepath(self, file_path: str) -> Path:
        r"""Convert the given string path to a Path object.

        If the provided path is not absolute, it is made relative to the
        default output directory. The filename part is sanitized to replace
        spaces and special characters with underscores, ensuring safe usage
        in downstream processing.

        Args:
            file_path (str): The file path to resolve.

        Returns:
            Path: A fully resolved (absolute) and sanitized Path object.
        """
        path_obj = Path(file_path)
        if not path_obj.is_absolute():
            path_obj = self.work_dir / path_obj

        sanitized_filename = self._sanitize_filename(path_obj.name)
        path_obj = path_obj.parent / sanitized_filename
        return path_obj.resolve()

    def _create_backup(self, file_path: Path) -> None:
        r"""Create a backup of the file if it exists and backup is enabled.

        Args:
            file_path (Path): Path to the file to backup.
        """
        if not self.backup_enabled or not file_path.exists():
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.parent / f"{file_path.name}.{timestamp}.bak"
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup at {backup_path}")

    async def edit_file(self, file_name: str, diff: str) -> None:  # TODO: return edit result!
        r"""Edit a file by applying the provided diff.

        Args:
            file_name (str): The name of the file to edit.
            diff (str): (required) One or more SEARCH/REPLACE blocks following this exact format:
                ```
                <<<<<<< SEARCH
                [exact content to find]
                =======
                [new content to replace with]
                >>>>>>> REPLACE
                ```
        """
        resolved_path = self._resolve_filepath(file_name)
        self._create_backup(resolved_path)

        try:
            with open(resolved_path, 'r', encoding=self.default_encoding) as f:
                content = f.read()
            modified_content = content
            pattern = r'<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE'
            # Use re.DOTALL to make '.' match newlines as well
            matches = re.findall(pattern, diff, re.DOTALL)
            
            if not matches:
                logger.warning("No valid diff blocks found in the provided diff")
                return
            
            # Apply each search/replace pair
            for search_text, replace_text in matches:
                if search_text in modified_content:
                    modified_content = modified_content.replace(search_text, replace_text)
                else:
                    logger.warning(f"Search text not found in file: {search_text[:50]}...")
            
            with open(resolved_path, 'w', encoding=self.default_encoding) as f:
                f.write(modified_content)
            logger.info(f"Successfully edited file: {resolved_path}")
        except Exception as e:
            logger.error(f"Error editing file {resolved_path}: {str(e)}")


    async def get_tools_map(self) -> dict[str, Callable]:
        return {
            "edit_file": self.edit_file,
        }

