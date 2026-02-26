import abc
import logging
from typing import Any

logger = logging.getLogger(__name__)


class MaintenanceTool(abc.ABC):
    """
    Base class for maintenance tools.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """User friendly name of the tool."""
        pass

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """Description of what the tool does."""
        pass

    @abc.abstractmethod
    async def run(self, **kwargs) -> dict[str, Any]:
        """Execute the maintenance task."""
        pass
