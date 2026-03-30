# infrastructure/adapters/libre_speed_adapter.py
"""
LibreSpeed Adapter
==================
Provides the interface and concrete implementation for executing speed
tests via the LibreSpeed CLI and retrieving server information.

Design
------
TestSpeedAdapter defines the abstract interface that all speed test
adapters must implement. This allows the service layer to remain
adapter-agnostic if additional providers are introduced in the future.

LibreSpeedAdapter is the concrete implementation for the LibreSpeed CLI
('librespeed-cli'). It encapsulates all subprocess argument configuration
and output parsing, exposing three operations to the rest of the system:
run_a_test(), get_servers(), and find_server_id().

Server ID Resolution
--------------------
The LibreSpeed CLI selects the best server automatically when no server
ID is provided. However, to ensure consistency across multiple samples
in the same session, the service layer resolves the chosen server's ID
after the first test and pins subsequent tests to that server.
find_server_id() supports this by matching the server URL from the test
result against the full server list returned by the CLI.

Adding a New Adapter
--------------------
    1. Create a class that inherits from TestSpeedAdapter.
    2. Implement run_a_test() returning an ISpeedTest instance.
    3. Register any CLI argument configurations as class-level constants.

Usage
-----
    from infrastructure.adapters.libre_speed_adapter import LibreSpeedAdapter

    result = LibreSpeedAdapter.run_a_test()
    server_id = LibreSpeedAdapter.find_server_id(result)
    servers = LibreSpeedAdapter.get_servers()

Raises
------
SpeedTestExecutionError
    If the CLI process fails or returns an unexpected output format.
ServerResolutionError
    If the server list is empty, the server URL is null, or no matching
    server ID can be found.
"""
import re
from schemas.is_speed_test import LibreSpeedTest, ISpeedTest, SpeedTestGoTest
from utils.subproccess_manager import SubProcessManager
from typing import List, Dict, Optional, Tuple, TypeVar, Generic
from utils.types import ServerData
from abc import ABC, abstractmethod
from utils.exceptions import SpeedTestExecutionError, ServerResolutionError

T = TypeVar('T', bound=ISpeedTest)

class TestSpeedAdapter(ABC,  Generic[T]):
    """
    Abstract interface for speed test adapters.

    All concrete adapter implementations must inherit from this class
    and implement run_a_test(), ensuring the service layer can operate
    against any provider without modification.
    """

    @classmethod
    @abstractmethod
    def run_a_test(cls, server_id: Optional[int] = None) -> T:
        """
        Execute a speed test and return the raw result.

        Returns
        -------
        ISpeedTest
            A provider-specific implementation of ISpeedTest populated
            with the raw CLI output.
        """
        pass
    
    @classmethod
    @abstractmethod
    def find_server_id(cls, record_test: T) -> int:
        pass

class SpeedTestGoAdapter(TestSpeedAdapter):
    
    _SUBPROCESS_ARGS_CONFIG: Dict[str, Tuple] = {
        'speed_test_best_server': ('speedtest-go', '--json'),
        'speed_test_by_server_id': ('speedtest-go', '--server', None, '--json'),
    }
    
    @classmethod
    def run_a_test(
        cls, server_id: Optional[int] = None
    ) -> SpeedTestGoTest:
        
        if server_id:
            process_args = list(
                cls._SUBPROCESS_ARGS_CONFIG['speed_test_by_server_id']
            )
            process_args[2] = str(server_id)
            process_args = tuple(process_args)
        else:
            process_args = cls._SUBPROCESS_ARGS_CONFIG['speed_test_best_server']
        
        process: Dict = SubProcessManager.run_subproccess(process_args)
        
        if not isinstance(process, Dict):
            raise SpeedTestExecutionError("The test did not return a dict")
        
        return SpeedTestGoTest(**process)
    
    @classmethod
    def find_server_id(cls, record_test: SpeedTestGoTest) -> int:
        return int(record_test.get_server()['id'])
    
class LibreSpeedAdapter(TestSpeedAdapter):
    """
    Concrete adapter for the LibreSpeed CLI ('librespeed-cli').

    Never instantiate this class. All members are class-level.
    """

    # CLI argument configurations keyed by operation name.
    # None at index 2 of 'speed_test_by_server_id' is a placeholder
    # for the server ID, populated at runtime in run_a_test().
    _SUBPROCCESS_ARGS_CONFIG: Dict[str, Tuple] = {
        'speed_test_best_server': ('librespeed-cli', '--json'),
        'speed_test_by_server_id': ('librespeed-cli', '--server', None, '--json'),
        'list_server': ('librespeed-cli', '--list')
    }

    # Regex pattern to extract server ID and URL from the CLI list output.
    # Group 1 — (\d+)         : Captures the numeric server ID.
    # Literal — :             : Matches the colon separator.
    # Skip    — .*?           : Lazily skips the server name.
    # Literal — \(            : Matches the opening parenthesis.
    # Group 2 — (https?://.*?): Captures the server URL (http or https).
    # Literal — \)            : Matches the closing parenthesis.
    _GET_SERVER_PATTER = r"(\d+):.*?\((https?://.*?)\)"

    @classmethod
    def run_a_test(
        cls, server_id: Optional[int] = None
    ) -> LibreSpeedTest:
        """
        Execute a speed test and return the raw result as a LibreSpeedTest.

        If a server_id is provided, the test targets that specific server.
        Otherwise, the CLI selects the best available server automatically.

        Parameters
        ----------
        server_id : Optional[int]
            The ID of the server to test against. If None, the CLI
            selects the best server automatically.

        Returns
        -------
        LibreSpeedTest
            The raw speed test result populated from the CLI JSON output.

        Raises
        ------
        SpeedTestExecutionError
            If the CLI exits with an error, or if the output is not a
            list of result dictionaries as expected.
        """
        if server_id:
            # Inject the server ID into the placeholder at index 2.
            process_args = list(
                cls._SUBPROCCESS_ARGS_CONFIG['speed_test_by_server_id']
            )
            process_args[2] = str(server_id)
            process_args = tuple(process_args)

        else:
            process_args = cls._SUBPROCCESS_ARGS_CONFIG['speed_test_best_server']

        process: List[Dict] = SubProcessManager.run_subproccess(process_args)

        if not isinstance(process, List):
            raise SpeedTestExecutionError("The test did not return a list")

        if not all(isinstance(result, Dict) for result in process):
            raise SpeedTestExecutionError("The test did not return the result JSON")

        return LibreSpeedTest(**process[0])

    @classmethod
    def get_servers(cls) -> List[ServerData]:
        """
        Retrieve the list of available LibreSpeed servers.

        Parses the plain-text output of 'librespeed-cli --list' using
        a regex pattern to extract server IDs and URLs.

        Returns
        -------
        List[ServerData]
            A list of dictionaries each containing 'id' and 'url' keys.

        Raises
        ------
        ServerResolutionError
            If the CLI returns an empty server list.
        """
        result: str = SubProcessManager.run_subproccess(
            cls._SUBPROCCESS_ARGS_CONFIG['list_server']
        )

        if not result:
            raise ServerResolutionError("No servers found")

        matches = re.findall(
            cls._GET_SERVER_PATTER, result, re.IGNORECASE
        )

        return [{"id": id, "url": url} for id, url in matches]

    @classmethod
    def find_server_id(cls, record_test: LibreSpeedTest) -> int:
        """
        Resolve the server ID used in a given test result.

        Extracts the server URL from the test result and matches it
        against the full server list returned by the CLI.

        Parameters
        ----------
        record_test : LibreSpeedTest
            The test result whose server ID is to be resolved.

        Returns
        -------
        int
            The numeric ID of the matched server.

        Raises
        ------
        ServerResolutionError
            If the server URL is null or empty, or if no server in the
            list matches the URL from the test result.
        """
        url_target = record_test.get_server()['url']

        if not url_target:
            raise ServerResolutionError("The server's URL must not be NULL")

        server_map = cls.get_servers()

        for server_data in server_map:
            if server_data['url'] == url_target:
                return int(server_data['id'])

        raise ServerResolutionError(
            f"Could not find server ID for URL: {url_target}"
        )