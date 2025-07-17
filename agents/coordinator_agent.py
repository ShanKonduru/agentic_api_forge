# agents/coordinator.py
from typing import Dict, Any
from agents.base_agent import Agent
from agents.parser_agent import ParserAgent
from agents.generator_agents import PythonClientGeneratorAgent, FlaskGeneratorAgent
from agents.test_generator_agent import TestGeneratorAgent

class CoordinatorAgent(Agent):
    """
    Agent responsible for coordinating the code generation process
    """
    def __init__(self):
        self.parser_agent = ParserAgent()
        self.python_client_agent = PythonClientGeneratorAgent()
        self.flask_agent = FlaskGeneratorAgent()
        self.test_agent = TestGeneratorAgent()

    # agents/coordinator.py
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Coordinate the code generation process

        Args:
            raml_content: String containing RAML specification
            base_dir: Base directory for resolving includes
            generate_client: Boolean indicating whether to generate Python client code
            generate_flask: Boolean indicating whether to generate Flask API code
            generate_tests: Boolean indicating whether to generate test code

        Returns:
            Dictionary containing generated code
        """
        raml_content = kwargs.get('raml_content')
        base_dir = kwargs.get('base_dir')
        generate_client = kwargs.get('generate_client', False)
        generate_flask = kwargs.get('generate_flask', False)
        generate_tests = kwargs.get('generate_tests', False)

        if not raml_content:
            raise ValueError("RAML content is required")

        results = {
            'status': 'success',
            'client_code': None,
            'flask_code': None,
            'test_code': None
        }

        try:
            # Parse RAML
            parse_result = self.parser_agent.run(raml_content=raml_content, base_dir=base_dir)
            if parse_result['status'] != 'success':
                return parse_result

            # Make sure parsed_data exists in the result
            if 'parsed_data' not in parse_result:
                return {
                    'status': 'error',
                    'message': "Parser did not return parsed data"
                }

            parsed_raml = parse_result['parsed_data']

            # Generate Python client code if requested
            if generate_client:
                client_result = self.python_client_agent.run(parsed_raml=parsed_raml)
                if client_result['status'] != 'success':
                    results['client_status'] = 'error'
                    results['client_message'] = client_result.get('message', 'Unknown error')
                else:
                    results['client_code'] = client_result['code']

            # Generate Flask API code if requested
            if generate_flask:
                flask_result = self.flask_agent.run(parsed_raml=parsed_raml)
                if flask_result['status'] != 'success':
                    results['flask_status'] = 'error'
                    results['flask_message'] = flask_result.get('message', 'Unknown error')
                else:
                    results['flask_code'] = flask_result['code']

            # Generate test code if requested
            if generate_tests:
                test_result = self.test_agent.run(parsed_raml=parsed_raml)
                if test_result['status'] != 'success':
                    results['test_status'] = 'error'
                    results['test_message'] = test_result.get('message', 'Unknown error')
                else:
                    results['test_code'] = test_result['code']

            return results

        except Exception as e:
            import traceback
            return {
                'status': 'error',
                'message': f"Code generation failed: {str(e)}",
                'traceback': traceback.format_exc()
            }
