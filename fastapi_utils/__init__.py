from importlib.metadata import version

from .cbv_base import Api, Resource, set_responses, take_init_parameters

__version__ = version("fastapi_utils")

__all__ = [
    "Api",
    "Resource",
    "set_responses",
    "take_init_parameters",
]
