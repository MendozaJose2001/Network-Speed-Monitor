# utils/subproccess_manager.py
"""
Subprocess Execution Utilities
===============================
Handles the execution of external CLI processes and parsing of
their output. Used primarily to invoke the LibreSpeed CLI and
capture its results.

Design
------
All functionality is encapsulated in the SubProcessManager class,
which is never instantiated. Its methods operate at the class level,
keeping the interface explicit at the call site:
SubProcessManager.run_subprocess(args).

Output is parsed as JSON when possible. If parsing fails, the raw
string output is returned instead, allowing callers to handle both
structured and unstructured CLI responses.

Usage
-----
    from utils.subprocess_manager import SubProcessManager

    result = SubProcessManager.run_subprocess(('librespeed-cli', '--json'))

Raises
------
SpeedTestExecutionError
    If the subprocess exits with a non-zero return code.
"""
import subprocess
import json
from typing import Tuple, Any
from utils.exceptions import SpeedTestExecutionError


class SubProcessManager:
    """
    Namespace for external process execution utilities.
    Never instantiate this class. All members are class-level.
    """

    _CAPTURE_OUTPUT = True
    _TEXT_ = True

    @classmethod
    def run_subproccess(cls, arg: Tuple[str]) -> Any:
        """
        Execute an external CLI command and return its parsed output.

        Attempts to parse stdout as JSON. If parsing fails, returns
        the raw string output. Falls back to stderr if stdout is empty.

        Parameters
        ----------
        arg : Tuple[str]
            The command and its arguments to execute as a subprocess.

        Returns
        -------
        Any
            Parsed JSON object if the output is valid JSON,
            otherwise the raw string output.

        Raises
        ------
        SpeedTestExecutionError
            If the subprocess exits with a non-zero return code,
            wrapping the stderr message for context.

        Example
        -------
            >>> SubProcessManager.run_subprocess(('librespeed-cli', '--json'))
            [{'timestamp': '...', 'download': 95.4, ...}]
        """
        process = subprocess.run(
            args=arg,
            capture_output=True,
            text=True)

        if process.returncode != 0:
            raise SpeedTestExecutionError(
                f"CLI execution failed: {process.stderr}"
                )

        # Fall back to stderr if stdout is empty (some CLI tools write there).
        result = process.stdout if process.stdout.strip() else process.stderr

        try:
            return json.loads(result)

        except (json.JSONDecodeError, TypeError):
            return result