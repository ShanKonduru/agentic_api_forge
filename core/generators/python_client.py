# core/generators/python_client.py
from typing import Dict, Any, List
from core.generators.base import CodeGenerator
import re

class PythonClientGenerator(CodeGenerator):
    """
    Generates Python client code from parsed RAML
    """
    def generate(self) -> str:
        """
        Generate Python client code

        Returns:
            Python client code as a string
        """
        api_name = self.parsed_raml.get("title", "API")
        version = self.parsed_raml.get("version", "v1")
        endpoints = self.parsed_raml.get("endpoints", [])
        endpoint_details = self.parsed_raml.get("endpoint_details", {})

        # Clean up API name for class name
        class_name = ''.join(word.capitalize() for word in api_name.split())

        code = f"""
import requests
from typing import Dict, Any, Optional, List, Union

class {class_name}Client:
    \"\"\"
    Python client for {api_name} {version}
    Generated from RAML specification
    \"\"\"

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        \"\"\"
        Initialize the API client

        Args:
            base_url: The base URL for the API
            api_key: Optional API key for authentication
        \"\"\"
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key

    def get_headers(self) -> Dict[str, str]:
        \"\"\"
        Get the headers to use for API requests

        Returns:
            Dictionary of headers
        \"\"\"
        headers = {{"Content-Type": "application/json"}}
        if self.api_key:
            headers["Authorization"] = f"Bearer {{self.api_key}}"
        return headers

"""

        # Generate methods for each endpoint
        for endpoint in endpoints:
            endpoint_detail = endpoint_details.get(endpoint, {})
            methods = endpoint_detail.get('methods', {})

            for http_method, method_info in methods.items():
                method_name = self._get_method_name(http_method, endpoint)
                description = method_info.get('description', f'{http_method.upper()} {endpoint}')

                # Determine parameters based on method and endpoint
                params = []
                doc_params = []

                # Add path parameters
                path_params = self._extract_path_params(endpoint)
                for param in path_params:
                    params.append(f"{param}: str")
                    doc_params.append(f"            {param}: Path parameter for {param}")

                # Add query parameters for GET requests
                if http_method.lower() == 'get':
                    query_params = method_info.get('queryParameters', {})
                    if query_params:
                        params.append("params: Optional[Dict[str, Any]] = None")
                        doc_params.append("            params: Query parameters")

                # Add body for POST/PUT/PATCH requests
                if http_method.lower() in ['post', 'put', 'patch']:
                    params.append("data: Dict[str, Any]")
                    doc_params.append("            data: Request body data")

                # Generate the method
                code += f"""
    def {method_name}({', '.join(['self'] + params)}) -> Dict[str, Any]:
        \"\"\"
        {description}

        Args:
{chr(10).join(doc_params) if doc_params else '            None'}

        Returns:
            API response as a dictionary
        \"\"\"
"""

                # Generate the URL with path parameters
                if path_params:
                    url_parts = []
                    path_parts = endpoint.split('/')
                    for part in path_parts:
                        if part.startswith('{') and part.endswith('}'):
                            param_name = part[1:-1]
                            url_parts.append(f"{{{param_name}}}")
                        elif part:
                            url_parts.append(part)

                    url_format = '/'.join(url_parts)
                    code += f"        url = f\"{{self.base_url}}/{url_format}\"\n"
                else:
                    code += f"        url = f\"{{self.base_url}}{endpoint}\"\n"

                # Generate the request
                if http_method.lower() == 'get':
                    code += """
        response = requests.get(
            url, 
            headers=self.get_headers(),
            params=params if params else None
        )
"""
                elif http_method.lower() == 'post':
                    code += """
        response = requests.post(
            url, 
            headers=self.get_headers(),
            json=data
        )
"""
                elif http_method.lower() == 'put':
                    code += """
        response = requests.put(
            url, 
            headers=self.get_headers(),
            json=data
        )
"""
                elif http_method.lower() == 'delete':
                    code += """
        response = requests.delete(
            url, 
            headers=self.get_headers()
        )
"""
                elif http_method.lower() == 'patch':
                    code += """
        response = requests.patch(
            url, 
            headers=self.get_headers(),
            json=data
        )
"""

                # Handle response
                code += """
        response.raise_for_status()  # Raise exception for 4XX/5XX responses

        try:
            return response.json()
        except ValueError:
            return {"status": "success", "status_code": response.status_code}
"""

        # Add error handling methods
        code += """
    def _handle_error(self, response):
        \"\"\"
        Handle error responses

        Args:
            response: The response object

        Raises:
            HTTPError: If the response contains an error
        \"\"\"
        if 400 <= response.status_code < 600:
            try:
                error_msg = response.json().get('message', str(response.status_code))
            except ValueError:
                error_msg = str(response.status_code)

            raise requests.HTTPError(f"Error {response.status_code}: {error_msg}", response=response)
"""

        return code

    def _get_method_name(self, http_method: str, path: str) -> str:
        """
        Generate a method name from HTTP method and path

        Args:
            http_method: The HTTP method (get, post, etc.)
            path: The endpoint path

        Returns:
            A method name suitable for use in code
        """
        # Remove leading and trailing slashes
        clean_path = path.strip('/')

        # Replace slashes with underscores
        resource_name = clean_path.replace('/', '_')

        # Handle path parameters (e.g., /{id})
        resource_name = resource_name.replace('{', '').replace('}', '')

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