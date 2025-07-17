# core/parser.py
from typing import Dict, Any, List
import yaml
import re
import os

class RAMLParser:
    """
    Parses RAML content into structured data
    """
    def __init__(self):
        self.parsed_data = None

    # Then modify the parse method in the RAMLParser class:
    def parse(self, raml_content: str, base_dir: str = None) -> Dict[str, Any]:
        """
        Parse RAML content into a structured dictionary

        Args:
            raml_content: String containing RAML specification
            base_dir: Base directory for resolving !include directives

        Returns:
            Dictionary containing parsed RAML data
        """
        try:
            print(f"Parsing RAML content with base_dir: {base_dir}")

            # Pre-process !include directives
            processed_content = self._process_includes(raml_content, base_dir)

            # Parse RAML content (YAML format)
            raw_data = yaml.safe_load(processed_content)

            if not raw_data:
                raise ValueError("RAML content is empty or invalid")

            # Extract API information
            api_info = {
                "title": raw_data.get("title", "API"),
                "version": raw_data.get("version", "v1"),
                "baseUri": raw_data.get("baseUri", ""),
                "protocols": raw_data.get("protocols", []),
                "mediaType": raw_data.get("mediaType", [])
            }

            # Extract endpoints and their details
            endpoints = []
            endpoint_details = {}

            # Process resources
            for path, resource_data in raw_data.items():
                if path.startswith('/'):
                    endpoints.append(path)
                    endpoint_details[path] = self._process_resource(path, resource_data)

                    # Process nested resources
                    nested_endpoints, nested_details = self._process_nested_resources(path, resource_data)
                    endpoints.extend(nested_endpoints)
                    endpoint_details.update(nested_details)

            # Combine all data
            parsed_data = {
                **api_info,
                "endpoints": endpoints,
                "endpoint_details": endpoint_details
            }

            print(f"Successfully parsed RAML with {len(endpoints)} endpoints")
            return parsed_data

        except Exception as e:
            print(f"Error parsing RAML: {str(e)}")
            raise ValueError(f"Failed to parse RAML content: {str(e)}")
    
    # core/parser.py
    def _process_resource(self, path: str, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a RAML resource

        Args:
            path: The resource path
            resource_data: Resource data from RAML

        Returns:
            Processed resource data
        """
        methods = {}

        # Process HTTP methods
        for key, value in resource_data.items():
            if key in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
                methods[key] = self._process_method(value)

        return {
            "methods": methods,
            "description": resource_data.get("description", ""),
            "displayName": resource_data.get("displayName", path)
        }

    def _process_method(self, method_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a RAML method

        Args:
            method_data: Method data from RAML

        Returns:
            Processed method data
        """
        if not method_data:
            return {}

        # Extract basic method info
        method_info = {
            "description": method_data.get("description", ""),
            "queryParameters": method_data.get("queryParameters", {}),
            "headers": method_data.get("headers", {})
        }

        # Process request body
        if "body" in method_data:
            method_info["body"] = method_data["body"]

        # Process responses
        if "responses" in method_data:
            method_info["responses"] = {}
            for status_code, response_data in method_data["responses"].items():
                method_info["responses"][status_code] = response_data

        return method_info

    def _process_nested_resources(self, parent_path: str, resource_data: Dict[str, Any]) -> tuple[List[str], Dict[str, Any]]:
        """
        Process nested resources

        Args:
            parent_path: The parent resource path
            resource_data: Resource data from RAML

        Returns:
            Tuple containing:
                - List of nested endpoint paths
                - Dictionary of nested endpoint details
        """
        nested_endpoints = []
        nested_details = {}

        for key, value in resource_data.items():
            if key.startswith('/'):
                # This is a nested resource
                full_path = parent_path + key
                nested_endpoints.append(full_path)
                nested_details[full_path] = self._process_resource(full_path, value)

                # Recursively process deeper nested resources
                deeper_endpoints, deeper_details = self._process_nested_resources(full_path, value)
                nested_endpoints.extend(deeper_endpoints)
                nested_details.update(deeper_details)

        return nested_endpoints, nested_details
    
    # Add this new method to the RAMLParser class:
    def _process_includes(self, content: str, base_dir: str = None) -> str:
        """
        Process !include directives in RAML content

        Args:
            content: RAML content
            base_dir: Base directory for resolving includes

        Returns:
            Processed RAML content with includes resolved
        """
        if base_dir is None:
            base_dir = os.getcwd()

        # Regular expression to find !include directives
        include_pattern = r'!include\s+([^\s]+)'

        def replace_include(match):
            include_path = match.group(1)
            # Resolve path relative to base_dir
            full_path = os.path.join(base_dir, include_path)

            try:
                with open(full_path, 'r') as include_file:
                    included_content = include_file.read()

                # If the included file is YAML, we need to indent it properly
                if include_path.endswith(('.yaml', '.yml', '.raml')):
                    # Convert to YAML string representation
                    included_yaml = yaml.safe_load(included_content)
                    return yaml.dump(included_yaml)
                else:
                    # For other files, return as string literal
                    return f'"{included_content}"'
            except Exception as e:
                # If we can't read the file, return a placeholder
                return f'"ERROR: Could not include {include_path}: {str(e)}"'

        # Replace all !include directives
        processed_content = re.sub(include_pattern, replace_include, content)
        return processed_content

    def _extract_endpoint_details(self, path: str, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract details for a specific endpoint

        Args:
            path: The endpoint path
            resource_data: The resource data from the RAML file

        Returns:
            Dictionary containing endpoint details
        """
        methods = {}

        # Extract HTTP methods (GET, POST, PUT, DELETE, etc.)
        for method_name, method_data in resource_data.items():
            if method_name in ['get', 'post', 'put', 'delete', 'patch']:
                method_info = {
                    'description': method_data.get('description', f'{method_name.upper()} {path}'),
                    'responses': {},
                    'queryParameters': {},
                    'uriParameters': {},
                    'body': {}
                }

                # Extract responses
                if 'responses' in method_data:
                    for status_code, response_data in method_data['responses'].items():
                        method_info['responses'][status_code] = {
                            'description': response_data.get('description', ''),
                            'body': response_data.get('body', {})
                        }

                # Extract query parameters
                if 'queryParameters' in method_data:
                    method_info['queryParameters'] = method_data['queryParameters']

                # Extract URI parameters
                if 'uriParameters' in method_data:
                    method_info['uriParameters'] = method_data['uriParameters']

                # Extract request body
                if 'body' in method_data:
                    method_info['body'] = method_data['body']

                methods[method_name] = method_info

        # Extract nested resources
        nested_resources = {}
        for key, value in resource_data.items():
            if key.startswith('/'):
                nested_path = path + key
                nested_resources[nested_path] = self._extract_endpoint_details(nested_path, value)

        return {
            'methods': methods,
            'nested_resources': nested_resources
        }

    def get_resource_name(self, path: str) -> str:
        """
        Convert a path to a resource name

        Args:
            path: The endpoint path

        Returns:
            A resource name suitable for use in code
        """
        # Remove leading and trailing slashes
        path = path.strip('/')

        # Replace slashes with underscores
        resource_name = path.replace('/', '_')

        # Handle path parameters (e.g., /{id})
        resource_name = re.sub(r'{([^}]+)}', r'by_\1', resource_name)

        return resource_name

    def get_method_name(self, http_method: str, path: str) -> str:
        """
        Generate a method name from HTTP method and path

        Args:
            http_method: The HTTP method (get, post, etc.)
            path: The endpoint path

        Returns:
            A method name suitable for use in code
        """
        resource_name = self.get_resource_name(path)

        if http_method.lower() == 'get':
            if path.endswith('}'):
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