import json
from typing import Any, Dict, List

from loguru import logger


class BaseOutput:
    """
    BaseOutput is a class that defines the interface for all output classes.
    """

    def __init__(self, fields: List[str]):
        self.fields = fields

    def write_output(self, value: Dict[str, Any]) -> None:
        logger.info(json.dumps(value, indent=4))
