import asyncio
import base64
import contextlib
import glob
import io
import os
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ..config import ToolkitConfig
from .base import AsyncBaseToolkit

# Used to clean ANSI escape sequences
ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def _execute_python_code_sync(code: str, workdir: str):
    """
    Synchronous execution of Python code.
    This function is intended to be run in a separate thread.
    """
    original_dir = os.getcwd()
    try:
        # Clean up code format
        code_clean = code.strip()
        if code_clean.startswith("```python"):
            code_clean = code_clean.split("```python")[1].split("```")[0].strip()

        # Create and change to working directory
        os.makedirs(workdir, exist_ok=True)
        os.chdir(workdir)

        # Get file list before execution
        files_before = set(glob.glob("*"))

        # Create a new IPython shell instance
        from IPython.core.interactiveshell import InteractiveShell
        from traitlets.config.loader import Config

        InteractiveShell.clear_instance()

        config = Config()
        config.HistoryManager.enabled = False
        config.HistoryManager.hist_file = ":memory:"

        shell = InteractiveShell.instance(config=config)

        if hasattr(shell, "history_manager"):
            shell.history_manager.enabled = False

        output = io.StringIO()
        error_output = io.StringIO()

        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error_output):
            shell.run_cell(code_clean)

            if plt.get_fignums():
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format="png")
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode("utf-8")
                plt.close()

                image_name = "output_image.png"
                counter = 1
                while os.path.exists(image_name):
                    image_name = f"output_image_{counter}.png"
                    counter += 1

                with open(image_name, "wb") as f:
                    f.write(base64.b64decode(img_base64))

        stdout_result = output.getvalue()
        stderr_result = error_output.getvalue()

        stdout_result = ANSI_ESCAPE.sub("", stdout_result)
        stderr_result = ANSI_ESCAPE.sub("", stderr_result)

        files_after = set(glob.glob("*"))
        new_files = list(files_after - files_before)
        new_files = [os.path.join(workdir, f) for f in new_files]

        try:
            shell.atexit_operations = lambda: None
            if hasattr(shell, "history_manager") and shell.history_manager:
                shell.history_manager.enabled = False
                shell.history_manager.end_session = lambda: None
            InteractiveShell.clear_instance()
        except Exception:  # pylint: disable=broad-except
            pass

        return {
            "success": False
            if "Error" in stderr_result or ("Error" in stdout_result and "Traceback" in stdout_result)
            else True,
            "message": f"Code execution completed\nOutput:\n{stdout_result.strip()}"
            if stdout_result.strip()
            else "Code execution completed, no output",
            "status": True,
            "files": new_files,
            "error": stderr_result.strip() if stderr_result.strip() else "",
        }
    except Exception as e:  # pylint: disable=broad-except
        return {
            "success": False,
            "message": f"Code execution failed, error message:\n{str(e)}",
            "status": False,
            "files": [],
            "error": str(e),
        }
    finally:
        os.chdir(original_dir)


class PythonExecutorToolkit(AsyncBaseToolkit):
    """
    A tool for executing Python code in a sandboxed environment.
    """

    def __init__(self, config: ToolkitConfig | dict | None = None):
        super().__init__(config)

    async def get_tools_map(self) -> dict[str, callable]:
        return {
            "execute_python_code": self.execute_python_code,
        }

    async def execute_python_code(self, code: str, workdir: str = "./run_workdir", timeout: int = 30) -> dict:
        """
        Executes Python code and returns the output.

        Args:
            code (str): The Python code to execute.
            workdir (str): The working directory for the execution. Defaults to "./run_workdir".
            timeout (int): The execution timeout in seconds. Defaults to 30.

        Returns:
            dict: A dictionary containing the execution results.
        """
        loop = asyncio.get_running_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(
                    None,  # Use the default thread pool executor
                    _execute_python_code_sync,
                    code,
                    workdir,
                ),
                timeout=timeout,
            )
        except TimeoutError:
            return {
                "success": False,
                "message": f"Code execution timed out ({timeout} seconds)",
                "stdout": "",
                "stderr": "",
                "status": False,
                "output": "",
                "files": [],
                "error": f"Code execution timed out ({timeout} seconds)",
            }
