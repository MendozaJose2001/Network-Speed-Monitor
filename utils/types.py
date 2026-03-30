# utils/types.py
"""
Shared Type Aliases
===================
Defines reusable type aliases used across the project to improve
readability and consistency in type annotations.

Types
-----
DataClassProtocol : Union[Type[Any], Any]
    Represents either a dataclass class or an instance of one.
    Used primarily in HeaderManager to accept both forms without
    restricting the interface unnecessarily.
    TODO: Replace with a more precise Protocol-based definition
    once the interface stabilizes.

StrFloat : Union[str, float]
    Represents values that may arrive as either a string or a float.
    Common in raw speed test results where numeric fields are
    sometimes serialized as strings by the CLI output.

ServerData : Dict[str, str]
    Represents a server entry returned by the LibreSpeed CLI,
    containing string key-value pairs such as 'id' and 'url'.
"""
from typing import (
    Union, Any, Type, Dict
    )

# Represents a dataclass class or instance. See module docstring for details.
DataClassProtocol = Union[Type[Any], Any]

# Numeric value that may arrive serialized as a string from the CLI output.
StrFloat = Union[str, float]

# Server entry from the LibreSpeed CLI, keyed by field name.
ServerData = Dict[str, str]
