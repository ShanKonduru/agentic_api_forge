# agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class Agent(ABC):
    """
    Abstract base class for agents
    """
    @abstractmethod
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Run the agent

        Args:
            **kwargs: Keyword arguments for the agent

        Returns:
            Dictionary containing the agent's results
        """
        pass
