# core/generators/test_generator.py (Part 1)
from typing import Dict, Any, List
from .base import CodeGenerator
import re
import json

class PyTestGenerator(CodeGenerator):
    """
    Generates pytest test cases for REST APIs from parsed RAML
    """
    def generate(self) -> str:
        """
        Generate pytest test cases for the API

        Returns:
            Pytest test code as a string
        """
        api_name = self.parsed_raml.get("title", "API")
        version = self.parsed_raml.get("version", "v1")
        endpoints = self.parsed_raml.get("endpoints", [])
        endpoint_details = self.parsed_raml.get("endpoint_details", {})

        # Start with imports and fixtures
        code = f"""
import pytest
import requests
import json
from unittest.mock import patch, MagicMock

# Base URL for testing - replace with your test server URL
BASE_URL = "http://localhost:5000"

# Test fixtures
@pytest.fixture
def api_client():
    \"\"\"Create a test client for the API\"\"\"
    class TestClient:
        def __init__(self, base_url):
            self.base_url = base_url
            self.session = requests.Session()

        def get_headers(self):
            return {{"Content-Type": "application/json"}}

    return TestClient(BASE_URL)

"""

        # Generate test cases for each endpoint
        for endpoint in endpoints:
            endpoint_detail = endpoint_details.get(endpoint, {})
            methods = endpoint_detail.get('methods', {})

            for http_method, method_info in methods.items():
                resource_name = self._get_resource_name(endpoint)
                method_name = self._get_method_name(http_method, endpoint)

                # Generate test class name
                test_class_name = f"Test{resource_name.capitalize()}{http_method.capitalize()}"

                # Generate sample data based on endpoint and method
                sample_data = self._generate_sample_data(endpoint, http_method, method_info)

                # Generate positive test cases
                code += f"""
# Positive test cases for {http_method.upper()} {endpoint}
class {test_class_name}Positive:
    def test_{method_name}_success(self, api_client):
        \"\"\"Test successful {http_method.upper()} request to {endpoint}\"\"\"
"""

                # Generate test implementation based on HTTP method
                if http_method.lower() == 'get':
                    if '{' in endpoint and '}' in endpoint:
                        # Test for getting a single resource
                        code += self._generate_get_by_id_test(endpoint, method_info)
                    else:
                        # Test for getting a collection
                        code += self._generate_get_collection_test(endpoint, method_info)
                elif http_method.lower() == 'post':
                    code += self._generate_post_test(endpoint, method_info, sample_data)
                elif http_method.lower() == 'put':
                    code += self._generate_put_test(endpoint, method_info, sample_data)
                elif http_method.lower() == 'delete':
                    code += self._generate_delete_test(endpoint, method_info)
                elif http_method.lower() == 'patch':
                    code += self._generate_patch_test(endpoint, method_info, sample_data)

                # Generate negative test cases
                code += f"""

# Negative test cases for {http_method.upper()} {endpoint}
class {test_class_name}Negative:
    def test_{method_name}_error(self, api_client):
        \"\"\"Test error handling for {http_method.upper()} request to {endpoint}\"\"\"
"""

                # Generate negative test implementation
                code += self._generate_negative_test(http_method, endpoint, method_info)

        return code

# core/generators/test_generator.py (Part 2)
    def _get_resource_name(self, path: str) -> str:
        """
        Get a resource name from a path

        Args:
            path: The endpoint path

        Returns:
            Resource name
        """
        # Remove leading/trailing slashes
        clean_path = path.strip('/')

        # Replace slashes with underscores
        resource_name = clean_path.replace('/', '_')

        # Handle path parameters (e.g., /{id})
        resource_name = re.sub(r'{([^}]+)}', r'by_\1', resource_name)

        return resource_name

    def _get_method_name(self, http_method: str, path: str) -> str:
        """
        Generate a method name from HTTP method and path

        Args:
            http_method: The HTTP method (get, post, etc.)
            path: The endpoint path

        Returns:
            A method name suitable for use in code
        """
        resource_name = self._get_resource_name(path)

        if http_method.lower() == 'get':
            if '{' in path and '}' in path:
                return f"get_{resource_name}"
            return f"get_{resource_name}_list"
        elif http_method.lower() == 'post':
            return f"create_{resource_name}"
        elif http_method.lower() == 'put':
            return f"update_{resource_name}"
        elif http_method.lower() == 'delete':
            return f"delete_{resource_name}"
        elif http_method.lower() == 'patch':
            return f"patch_{resource_name}"
        else:
            return f"{http_method.lower()}_{resource_name}"

    def _extract_path_params(self, path: str) -> List[str]:
        """
        Extract path parameters from a URL path

        Args:
            path: The URL path

        Returns:
            List of path parameter names
        """
        params = []
        parts = path.split('/')

        for part in parts:
            if part.startswith('{') and part.endswith('}'):
                param_name = part[1:-1]
                params.append(param_name)

        return params

    # In _generate_sample_data method
    def _generate_sample_data(self, path: str, http_method: str, method_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate sample data for a request

        Args:
            path: The endpoint path
            http_method: The HTTP method
            method_info: Method information

        Returns:
            Sample data as a dictionary
        """
        sample_data = {}

        # Try to extract from request body schema or example
        if http_method.lower() in ['post', 'put', 'patch'] and 'body' in method_info:
            body_info = method_info['body']

            # Check if body_info is a dictionary
            if not isinstance(body_info, dict):
                print(f"Warning: Body info for {path} {http_method} is not a dictionary: {body_info}")
                return sample_data

            if 'application/json' in body_info:
                json_info = body_info['application/json']

                # Check if json_info is a dictionary
                if not isinstance(json_info, dict):
                    print(f"Warning: JSON info for {path} {http_method} is not a dictionary: {json_info}")
                    return sample_data

                if 'example' in json_info:
                    # Check if the example is a string that needs to be parsed
                    example = json_info['example']
                    if isinstance(example, str):
                        try:
                            return json.loads(example)
                        except json.JSONDecodeError:
                            # If it's not valid JSON, just return it as is
                            return {"example": example}
                    return example

        # If no example is available, generate sample data based on resource name
        resource_name = self._get_resource_name(path).replace('_', ' ').strip()

        if resource_name.endswith('s'):
            resource_name = resource_name[:-1]  # Singularize

        sample_data = {
            "name": f"Test {resource_name}",
            "description": f"This is a test {resource_name}",
        }

        # Add ID for PUT/PATCH/DELETE
        if http_method.lower() in ['put', 'patch', 'delete']:
            sample_data["id"] = 123

        return sample_data

    # core/generators/test_generator.py (Part 3)
    def _generate_get_by_id_test(self, path: str, method_info: Dict[str, Any]) -> str:
        """
        Generate test code for a GET method that retrieves a single resource

        Args:
            path: The endpoint path
            method_info: Method information

        Returns:
            Test implementation code
        """
        # Extract the ID parameter
        id_param = self._extract_path_params(path)[0]
        test_id = 123  # Example ID

        # Replace path parameters with actual values
        test_path = path.replace(f"{{{id_param}}}", str(test_id))

        code = f"""
        # Mock response data
        mock_response = {{
            "id": {test_id},
            "name": "Test Item",
            "description": "This is a test item"
        }}

        # Mock the requests.get method
        with patch('requests.Session.get') as mock_get:
            # Configure the mock to return a response with mock data
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_get.return_value = mock_response_obj

            # Make the request
            response = api_client.session.get(
                f"{{api_client.base_url}}{test_path}",
                headers=api_client.get_headers()
            )

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == {test_id}
            assert "name" in data
            assert "description" in data
        """

        return code

    def _generate_get_collection_test(self, path: str, method_info: Dict[str, Any]) -> str:
        """
        Generate test code for a GET method that retrieves a collection of resources

        Args:
            path: The endpoint path
            method_info: Method information

        Returns:
            Test implementation code
        """
        code = f"""
        # Mock response data
        mock_response = [
            {{
                "id": 1,
                "name": "Test Item 1",
                "description": "This is test item 1"
            }},
            {{
                "id": 2,
                "name": "Test Item 2",
                "description": "This is test item 2"
            }}
        ]

        # Mock the requests.get method
        with patch('requests.Session.get') as mock_get:
            # Configure the mock to return a response with mock data
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_get.return_value = mock_response_obj

            # Make the request
            response = api_client.session.get(
                f"{{api_client.base_url}}{path}",
                headers=api_client.get_headers()
            )

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0
            assert "id" in data[0]
            assert "name" in data[0]
        """

        return code
    
# core/generators/test_generator.py (Part 4)
    def _generate_post_test(self, path: str, method_info: Dict[str, Any], sample_data: Dict[str, Any]) -> str:
        """
        Generate test code for a POST method that creates a resource

        Args:
            path: The endpoint path
            method_info: Method information
            sample_data: Sample request data

        Returns:
            Test implementation code
        """
        # Convert sample data to a string representation for the code
        sample_data_str = json.dumps(sample_data, indent=4)

        code = f"""
        # Request data
        request_data = {sample_data_str}

        # Mock response data (usually includes an ID)
        mock_response = {{
            "id": 123,
            **request_data
        }}

        # Mock the requests.post method
        with patch('requests.Session.post') as mock_post:
            # Configure the mock to return a response with mock data
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 201
            mock_response_obj.json.return_value = mock_response
            mock_post.return_value = mock_response_obj

            # Make the request
            response = api_client.session.post(
                f"{{api_client.base_url}}{path}",
                headers=api_client.get_headers(),
                json=request_data
            )

            # Assertions
            assert response.status_code == 201
            data = response.json()
            assert "id" in data
            for key, value in request_data.items():
                assert data[key] == value
        """

        return code

    def _generate_put_test(self, path: str, method_info: Dict[str, Any], sample_data: Dict[str, Any]) -> str:
        """
        Generate test code for a PUT method that updates a resource

        Args:
            path: The endpoint path
            method_info: Method information
            sample_data: Sample request data

        Returns:
            Test implementation code
        """
        # Extract the ID parameter
        id_params = self._extract_path_params(path)
        test_id = 123  # Example ID

        # Replace path parameters with actual values
        test_path = path
        for param in id_params:
            test_path = test_path.replace(f"{{{param}}}", str(test_id))

        # Convert sample data to a string representation for the code
        sample_data_str = json.dumps(sample_data, indent=4)

        code = f"""
        # Request data
        request_data = {sample_data_str}

        # Mock response data
        mock_response = {{
            "id": {test_id},
            **request_data
        }}

        # Mock the requests.put method
        with patch('requests.Session.put') as mock_put:
            # Configure the mock to return a response with mock data
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_put.return_value = mock_response_obj

            # Make the request
            response = api_client.session.put(
                f"{{api_client.base_url}}{test_path}",
                headers=api_client.get_headers(),
                json=request_data
            )

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == {test_id}
            for key, value in request_data.items():
                assert data[key] == value
        """

        return code

# core/generators/test_generator.py (Part 5)
    def _generate_delete_test(self, path: str, method_info: Dict[str, Any]) -> str:
        """
        Generate test code for a DELETE method that deletes a resource

        Args:
            path: The endpoint path
            method_info: Method information

        Returns:
            Test implementation code
        """
        # Extract the ID parameter
        id_params = self._extract_path_params(path)
        test_id = 123  # Example ID

        # Replace path parameters with actual values
        test_path = path
        for param in id_params:
            test_path = test_path.replace(f"{{{param}}}", str(test_id))

        code = f"""
        # Mock response data
        mock_response = {{
            "message": "Resource deleted successfully"
        }}

        # Mock the requests.delete method
        with patch('requests.Session.delete') as mock_delete:
            # Configure the mock to return a response with mock data
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_delete.return_value = mock_response_obj

            # Make the request
            response = api_client.session.delete(
                f"{{api_client.base_url}}{test_path}",
                headers=api_client.get_headers()
            )

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
        """

        return code

    def _generate_patch_test(self, path: str, method_info: Dict[str, Any], sample_data: Dict[str, Any]) -> str:
        """
        Generate test code for a PATCH method that partially updates a resource

        Args:
            path: The endpoint path
            method_info: Method information
            sample_data: Sample request data

        Returns:
            Test implementation code
        """
        # Extract the ID parameter
        id_params = self._extract_path_params(path)
        test_id = 123  # Example ID

        # Replace path parameters with actual values
        test_path = path
        for param in id_params:
            test_path = test_path.replace(f"{{{param}}}", str(test_id))

        # For PATCH, we'll use a subset of the sample data
        patch_data = {}
        if sample_data:
            # Take the first field from sample data
            for key, value in sample_data.items():
                if key != "id":  # Skip ID field
                    patch_data[key] = value
                    break

        if not patch_data:
            patch_data = {"name": "Updated Name"}

        # Convert patch data to a string representation for the code
        patch_data_str = json.dumps(patch_data, indent=4)

        code = f"""
        # Request data (partial update)
        request_data = {patch_data_str}

        # Mock response data
        mock_response = {{
            "id": {test_id},
            **request_data
        }}

        # Mock the requests.patch method
        with patch('requests.Session.patch') as mock_patch:
            # Configure the mock to return a response with mock data
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_patch.return_value = mock_response_obj

            # Make the request
            response = api_client.session.patch(
                f"{{api_client.base_url}}{test_path}",
                headers=api_client.get_headers(),
                json=request_data
            )

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == {test_id}
            for key, value in request_data.items():
                assert data[key] == value
        """

        return code

    def _generate_negative_test(self, http_method: str, path: str, method_info: Dict[str, Any]) -> str:
        """
        Generate negative test code for error handling

        Args:
            http_method: The HTTP method
            path: The endpoint path
            method_info: Method information

        Returns:
            Test implementation code
        """
        # Choose an appropriate error scenario based on the HTTP method
        if http_method.lower() == 'get':
            # For GET, test resource not found (404)
            id_params = self._extract_path_params(path)
            if id_params:
                # Test for getting a non-existent resource
                test_id = 99999  # Non-existent ID
                test_path = path
                for param in id_params:
                    test_path = test_path.replace(f"{{{param}}}", str(test_id))

                code = f"""
        # Mock a 404 response
        with patch('requests.Session.get') as mock_get:
            # Configure the mock to return a 404 response
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.json.return_value = {{"error": "Resource not found"}}
            mock_get.return_value = mock_response

            # Make the request
            response = api_client.session.get(
                f"{{api_client.base_url}}{test_path}",
                headers=api_client.get_headers()
            )

            # Assertions
            assert response.status_code == 404
            data = response.json()
            assert "error" in data
        """
            else:
                # Test for invalid query parameters
                code = f"""
        # Mock a 400 response for invalid query parameters
        with patch('requests.Session.get') as mock_get:
            # Configure the mock to return a 400 response
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {{"error": "Invalid query parameters"}}
            mock_get.return_value = mock_response

            # Make the request with invalid parameters
            response = api_client.session.get(
                f"{{api_client.base_url}}{path}",
                headers=api_client.get_headers(),
                params={{"invalid_param": "invalid_value"}}
            )

            # Assertions
            assert response.status_code == 400
            data = response.json()
            assert "error" in data
        """

        elif http_method.lower() in ['post', 'put', 'patch']:
            # For POST/PUT/PATCH, test validation error (422)
            code = f"""
        # Mock a 422 validation error response
        with patch('requests.Session.{http_method.lower()}') as mock_method:
            # Configure the mock to return a 422 response
            mock_response = MagicMock()
            mock_response.status_code = 422
            mock_response.json.return_value = {{
                "error": "Validation error",
                "messages": {{"field": ["Field is required"]}}
            }}
            mock_method.return_value = mock_response

            # Make the request with invalid data
            response = api_client.session.{http_method.lower()}(
                f"{{api_client.base_url}}{path}",
                headers=api_client.get_headers(),
                json={{}}  # Empty data to trigger validation error
            )

            # Assertions
            assert response.status_code == 422
            data = response.json()
            assert "error" in data
            assert "messages" in data
        """

        elif http_method.lower() == 'delete':
            # For DELETE, test resource not found (404)
            id_params = self._extract_path_params(path)
            test_id = 99999  # Non-existent ID
            test_path = path
            for param in id_params:
                test_path = test_path.replace(f"{{{param}}}", str(test_id))

            code = f"""
        # Mock a 404 response
        with patch('requests.Session.delete') as mock_delete:
            # Configure the mock to return a 404 response
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.json.return_value = {{"error": "Resource not found"}}
            mock_delete.return_value = mock_response

            # Make the request
            response = api_client.session.delete(
                f"{{api_client.base_url}}{test_path}",
                headers=api_client.get_headers()
            )

            # Assertions
            assert response.status_code == 404
            data = response.json()
            assert "error" in data
        """

        else:
            # Generic error test
            code = f"""
        # Mock a 500 server error response
        with patch('requests.Session.{http_method.lower()}') as mock_method:
            # Configure the mock to return a 500 response
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.json.return_value = {{"error": "Internal server error"}}
            mock_method.return_value = mock_response

            # Make the request
            response = api_client.session.{http_method.lower()}(
                f"{{api_client.base_url}}{path}",
                headers=api_client.get_headers()
            )

            # Assertions
            assert response.status_code == 500
            data = response.json()
            assert "error" in data
        """

        return code

        