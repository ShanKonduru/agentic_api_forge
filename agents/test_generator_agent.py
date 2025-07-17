# agents/test_generator_agent.py
from typing import Dict, Any
from .base_agent import Agent
from core.generators.test_generator import PyTestGenerator

class TestGeneratorAgent(Agent):
    """
    Agent responsible for generating test code
    """
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Generate test code

        Args:
            parsed_raml: Dictionary containing parsed RAML data

        Returns:
            Dictionary containing generated test code
        """
        parsed_raml = kwargs.get('parsed_raml')
        if not parsed_raml:
            raise ValueError("Parsed RAML data is required")

        try:
            # Generate test code
            generator = PyTestGenerator(parsed_raml)
            code = generator.generate()

            return {
                'status': 'success',
                'code': code
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Failed to generate test code: {str(e)}"
            }