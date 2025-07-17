# agents/generator_agents.py
from typing import Dict, Any
from .base_agent import Agent
from core.generators.python_client import PythonClientGenerator
from core.generators.flask_generator import FlaskGenerator

class PythonClientGeneratorAgent(Agent):
    """
    Agent responsible for generating Python client code
    """
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Generate Python client code

        Args:
            parsed_raml: Dictionary containing parsed RAML data

        Returns:
            Dictionary containing generated code
        """
        parsed_raml = kwargs.get('parsed_raml')
        if not parsed_raml:
            raise ValueError("Parsed RAML data is required")

        try:
            # Generate Python client code
            generator = PythonClientGenerator(parsed_raml)
            code = generator.generate()

            return {
                'status': 'success',
                'code': code
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Failed to generate Python client code: {str(e)}"
            }

class FlaskGeneratorAgent(Agent):
    """
    Agent responsible for generating Flask API code
    """
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Generate Flask API code

        Args:
            parsed_raml: Dictionary containing parsed RAML data

        Returns:
            Dictionary containing generated code
        """
        parsed_raml = kwargs.get('parsed_raml')
        if not parsed_raml:
            raise ValueError("Parsed RAML data is required")

        try:
            # Generate Flask API code
            generator = FlaskGenerator(parsed_raml)
            code = generator.generate()

            return {
                'status': 'success',
                'code': code
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Failed to generate Flask API code: {str(e)}"
            }