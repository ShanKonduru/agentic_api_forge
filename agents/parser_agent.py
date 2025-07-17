# agents/parser_agent.py
from typing import Dict, Any
from .base_agent import Agent
from core.parser import RAMLParser

class ParserAgent(Agent):
    """
    Agent responsible for parsing RAML content
    """
    def __init__(self):
        self.parser = RAMLParser()

    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Parse RAML content

        Args:
            raml_content: String containing RAML specification
            base_dir: Optional base directory for resolving includes

        Returns:
            Dictionary containing parsed RAML data
        """
        raml_content = kwargs.get('raml_content')
        base_dir = kwargs.get('base_dir')

        if not raml_content:
            raise ValueError("RAML content is required")

        try:
            # Parse the RAML content
            parsed_data = self.parser.parse(raml_content, base_dir)

            return {
                'status': 'success',
                'parsed_data': parsed_data
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Failed to parse RAML: {str(e)}"
            }