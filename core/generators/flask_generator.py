# core/generators/flask.py - Part 1
from typing import Dict, Any, List
from .base import CodeGenerator
import re
import json

class FlaskGenerator(CodeGenerator):
    """
    Generator for Flask API code
    """

    def generate(self) -> str:
        """
        Generate Flask API code from parsed RAML

        Returns:
            Flask API code as a string
        """
        try:
            # Extract API information
            api_name = self.parsed_raml.get("title", "API")
            version = self.parsed_raml.get("version", "v1")

            # Check if endpoints and endpoint_details exist
            endpoints = self.parsed_raml.get("endpoints", [])
            endpoint_details = self.parsed_raml.get("endpoint_details", {})

            # Generate imports and app setup
            code = self._generate_imports()
            code += self._generate_app_setup(api_name, version)

            # Generate models
            code += self._generate_models(endpoints, endpoint_details)

            # Generate routes
            code += self._generate_routes(endpoints, endpoint_details)

            # Generate main block
            code += self._generate_main_block()

            return code
        except Exception as e:
            import traceback
            print(f"Error generating Flask API: {str(e)}")
            print(traceback.format_exc())
            raise ValueError(f"Failed to generate Flask API code: {str(e)}")

    def _generate_imports(self) -> str:
        """
        Generate import statements for Flask API

        Returns:
            Import statements as a string
        """
        return """from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

"""

    def _generate_app_setup(self, api_name: str, version: str) -> str:
        """
        Generate Flask app setup code

        Args:
            api_name: Name of the API
            version: API version

        Returns:
            App setup code as a string
        """
        # Convert API name to a valid Python variable name
        app_name = re.sub(r'[^a-zA-Z0-9]', '_', api_name.lower())

        return f"""# Create Flask app
app = Flask(__name__)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:////{app_name}.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# API information
API_NAME = "{api_name}"
API_VERSION = "{version}"

"""
# core/generators/flask.py - Part 2
    def _get_resource_name(self, path: str) -> str:
        """
        Extract resource name from path

        Args:
            path: The endpoint path

        Returns:
            Resource name
        """
        # Remove leading slash
        if path.startswith('/'):
            path = path[1:]

        # Split path by slashes
        parts = path.split('/')

        # Get the first part (resource name)
        resource_name = parts[0]

        # Remove any path parameters
        resource_name = re.sub(r'{.*?}', '', resource_name)

        # Clean up the name
        resource_name = re.sub(r'[^a-zA-Z0-9]', '_', resource_name)

        return resource_name

    def _get_model_class_name(self, resource_name: str) -> str:
        """
        Convert resource name to a model class name

        Args:
            resource_name: Resource name

        Returns:
            Model class name
        """
        # Remove trailing 's' if present (singularize)
        if resource_name.endswith('s'):
            resource_name = resource_name[:-1]

        # Capitalize each word
        words = resource_name.split('_')
        capitalized_words = [word.capitalize() for word in words]

        return ''.join(capitalized_words)

    def _map_type_to_sqlalchemy(self, field_type: str) -> str:
        """
        Map a field type to SQLAlchemy type

        Args:
            field_type: Field type

        Returns:
            SQLAlchemy type
        """
        type_mapping = {
            'string': 'db.String(255)',
            'integer': 'db.Integer',
            'number': 'db.Float',
            'boolean': 'db.Boolean',
            'array': 'db.PickleType',
            'object': 'db.JSON',
            'int': 'db.Integer',
            'float': 'db.Float',
            'bool': 'db.Boolean',
            'str': 'db.String(255)',
            'dict': 'db.JSON',
            'list': 'db.PickleType'
        }

        return type_mapping.get(field_type.lower(), 'db.String(255)')

    def _convert_path_to_flask(self, path: str) -> str:
        """
        Convert RAML path to Flask route path

        Args:
            path: RAML path

        Returns:
            Flask route path
        """
        # Replace RAML path parameters with Flask path parameters
        # RAML: /users/{userId}
        # Flask: /users/<userId>
        return re.sub(r'{(.*?)}', r'<\1>', path)

    def _extract_path_params(self, path: str) -> List[str]:
        """
        Extract path parameters from a path

        Args:
            path: The endpoint path

        Returns:
            List of path parameter names
        """
        # Find all path parameters
        params = re.findall(r'{(.*?)}', path)
        return params

# core/generators/flask.py - Part 3
    def _generate_models(self, endpoints: List[str], endpoint_details: Dict[str, Any]) -> str:
        """
        Generate Flask-SQLAlchemy models based on API endpoints

        Args:
            endpoints: List of API endpoints
            endpoint_details: Dictionary of endpoint details

        Returns:
            Model code as a string
        """
        if not endpoints:
            return "# No models generated - no endpoints found\n\n"

        models_code = "\n# Models\n"

        # Track models we've already generated
        generated_models = set()

        for endpoint in endpoints:
            # Skip if endpoint is not in details
            if endpoint not in endpoint_details:
                continue

            endpoint_detail = endpoint_details.get(endpoint)
            if not isinstance(endpoint_detail, dict):
                continue

            methods = endpoint_detail.get('methods')
            if not isinstance(methods, dict):
                continue

            # Extract resource name from endpoint
            resource_name = self._get_resource_name(endpoint)

            # Skip if we've already generated this model
            if resource_name in generated_models:
                continue

            # Look for POST or PUT methods to determine model structure
            model_fields = {}

            for method_name, method_info in methods.items():
                if method_name.lower() in ['post', 'put'] and isinstance(method_info, dict):
                    # Try to extract fields from request body
                    if 'body' in method_info and isinstance(method_info['body'], dict):
                        body = method_info['body']

                        # Look for JSON schema or example
                        if 'application/json' in body and isinstance(body['application/json'], dict):
                            json_info = body['application/json']

                            # Try to get schema
                            if 'schema' in json_info and isinstance(json_info['schema'], dict):
                                schema = json_info['schema']
                                if 'properties' in schema and isinstance(schema['properties'], dict):
                                    for field_name, field_info in schema['properties'].items():
                                        field_type = field_info.get('type', 'string')
                                        model_fields[field_name] = field_type

                            # If no schema, try to get example
                            elif 'example' in json_info:
                                example = json_info['example']

                                # If example is a string, try to parse it as JSON
                                if isinstance(example, str):
                                    try:
                                        example_dict = json.loads(example)
                                        if isinstance(example_dict, dict):
                                            for field_name, field_value in example_dict.items():
                                                field_type = type(field_value).__name__
                                                model_fields[field_name] = field_type
                                    except:
                                        # If parsing fails, just continue
                                        pass
                                # If example is already a dict
                                elif isinstance(example, dict):
                                    for field_name, field_value in example.items():
                                        field_type = type(field_value).__name__
                                        model_fields[field_name] = field_type

            # core/generators/flask.py - Part 4
            # If we found fields, generate a model
            if model_fields:
                model_class_name = self._get_model_class_name(resource_name)
                models_code += f"\nclass {model_class_name}(db.Model):\n"
                models_code += f"    __tablename__ = '{resource_name.lower()}'\n\n"
                models_code += "    id = db.Column(db.Integer, primary_key=True)\n"

                for field_name, field_type in model_fields.items():
                    if field_name != 'id':  # Skip id field as we already defined it
                        db_type = self._map_type_to_sqlalchemy(field_type)
                        models_code += f"    {field_name} = db.Column({db_type})\n"

                # Add __repr__ method
                models_code += "\n    def __repr__(self):\n"
                models_code += f"        return f'<{model_class_name} {{self.id}}>'\n"

                # Add to_dict method
                models_code += "\n    def to_dict(self):\n"
                models_code += "        return {\n"
                models_code += "            'id': self.id,\n"
                for field_name in model_fields:
                    if field_name != 'id':  # Skip id field as we already included it
                        models_code += f"            '{field_name}': self.{field_name},\n"
                models_code += "        }\n"

                # Mark as generated
                generated_models.add(resource_name)

        # If no models were generated, add a comment
        if not generated_models:
            models_code += "# No models could be generated from the API specification\n"

        return models_code + "\n"                                        
    
# core/generators/flask.py - Part 5
    def _generate_routes(self, endpoints: List[str], endpoint_details: Dict[str, Any]) -> str:
        """
        Generate Flask routes for the API endpoints

        Args:
            endpoints: List of API endpoints
            endpoint_details: Dictionary of endpoint details

        Returns:
            Flask routes code as a string
        """
        if not endpoints:
            return "# No routes generated - no endpoints found\n\n"

        routes_code = "\n# Routes\n"

        for endpoint in endpoints:
            # Skip if endpoint is not in details
            if endpoint not in endpoint_details:
                continue

            endpoint_detail = endpoint_details.get(endpoint)
            if not isinstance(endpoint_detail, dict):
                continue

            methods = endpoint_detail.get('methods')
            if not isinstance(methods, dict):
                continue

            # Generate route for this endpoint
            route_code = self._generate_route(endpoint, methods)
            routes_code += route_code

        return routes_code

# core/generators/flask.py - Part 6
    def _generate_route(self, path: str, methods: Dict[str, Any]) -> str:
        """
        Generate a Flask route for an API endpoint

        Args:
            path: The endpoint path
            methods: Dictionary of HTTP methods for this endpoint

        Returns:
            Flask route code as a string
        """
        if not methods:
            return ""

        # Convert RAML path to Flask route path
        flask_path = self._convert_path_to_flask(path)

        # Extract resource name
        resource_name = self._get_resource_name(path)
        model_class_name = self._get_model_class_name(resource_name)

        # Start route code
        route_code = f"\n@app.route('{flask_path}', methods=["

        # Add supported HTTP methods
        http_methods = [method.upper() for method in methods.keys()]
        route_code += ", ".join([f"'{method}'" for method in http_methods])
        route_code += "])\n"

        # Generate function name
        if '{' in path and '}' in path:
            # This is a path with parameters
            function_name = f"handle_{resource_name}_with_id"
        else:
            function_name = f"handle_{resource_name}"

        # Start function definition
        route_code += f"def {function_name}("

        # Add path parameters
        path_params = self._extract_path_params(path)
        if path_params:
            route_code += ", ".join(path_params)

        route_code += "):\n"

# core/generators/flask.py - Part 7
        # Function body
        route_code += "    # Get the HTTP method\n"
        route_code += "    method = request.method\n\n"

        # Handle different HTTP methods
        route_code += "    if method == 'GET':\n"
        if '{' in path and '}' in path:
            # This is a GET for a specific resource
            route_code += f"        # Get {resource_name} by ID\n"
            route_code += f"        item = {model_class_name}.query.get_or_404({path_params[0]})\n"
            route_code += "        return jsonify(item.to_dict())\n\n"
        else:
            # This is a GET for a collection
            route_code += f"        # Get all {resource_name}s\n"
            route_code += f"        items = {model_class_name}.query.all()\n"
            route_code += "        return jsonify([item.to_dict() for item in items])\n\n"

        if 'post' in methods:
            route_code += "    elif method == 'POST':\n"
            route_code += "        # Create a new item\n"
            route_code += "        data = request.json\n"
            route_code += f"        item = {model_class_name}(**data)\n"
            route_code += "        db.session.add(item)\n"
            route_code += "        db.session.commit()\n"
            route_code += "        return jsonify(item.to_dict()), 201\n\n"
# core/generators/flask.py - Part 8
        if 'put' in methods and '{' in path and '}' in path:
            route_code += "    elif method == 'PUT':\n"
            route_code += "        # Update an item\n"
            route_code += f"        item = {model_class_name}.query.get_or_404({path_params[0]})\n"
            route_code += "        data = request.json\n"
            route_code += "        for key, value in data.items():\n"
            route_code += "            setattr(item, key, value)\n"
            route_code += "        db.session.commit()\n"
            route_code += "        return jsonify(item.to_dict())\n\n"

        if 'delete' in methods and '{' in path and '}' in path:
            route_code += "    elif method == 'DELETE':\n"
            route_code += "        # Delete an item\n"
            route_code += f"        item = {model_class_name}.query.get_or_404({path_params[0]})\n"
            route_code += "        db.session.delete(item)\n"
            route_code += "        db.session.commit()\n"
            route_code += "        return jsonify({'message': 'Item deleted'})\n\n"

        if 'patch' in methods and '{' in path and '}' in path:
            route_code += "    elif method == 'PATCH':\n"
            route_code += "        # Partially update an item\n"
            route_code += f"        item = {model_class_name}.query.get_or_404({path_params[0]})\n"
            route_code += "        data = request.json\n"
            route_code += "        for key, value in data.items():\n"
            route_code += "            setattr(item, key, value)\n"
            route_code += "        db.session.commit()\n"
            route_code += "        return jsonify(item.to_dict())\n\n"

        route_code += "    return jsonify({'error': 'Method not allowed'}), 405\n"

        return route_code                    

# core/generators/flask.py - Part 9
    def _generate_main_block(self) -> str:
        """
        Generate the main block for the Flask app

        Returns:
            Main block code as a string
        """
        return """
# Create database tables
@app.before_first_request
def create_tables():
    db.create_all()

# Root endpoint
@app.route('/')
def index():
    return jsonify({
        'name': API_NAME,
        'version': API_VERSION,
        'message': 'Welcome to the API'
    })

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
"""
    