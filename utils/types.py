# utils/types.py

from typing import (
    Union, Any, Type, Dict
    )

DataClassProtocol = Union[Type[Any], Any] # Check later for a better option
StrFloat = Union[str,float]
ServerData = Dict[str,str]