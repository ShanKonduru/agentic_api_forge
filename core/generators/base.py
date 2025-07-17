# core/generators/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class CodeGenerator(ABC):
    """
    Abstract base class for code generators
    """
    def __init__(self, parsed_raml: Dict[str, Any]):
        self.parsed_raml = parsed_raml

    @abstractmethod
    def generate(self) -> str:
        """
        Generate code based on parsed RAML data

        Returns:
            Generated code as a string
        """
        pass