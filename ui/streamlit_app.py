# ui/streamlit_app.py
import streamlit as st
from typing import Dict, Any, Tuple


class StreamlitUI:
    """
    Streamlit UI for the RAML Code Generator
    """

    def __init__(self):
        """Initialize the UI"""
        # Try to set page configuration
        try:
            st.set_page_config(
                page_title="Agentic API Forge",
                page_icon="🔧",
                layout="wide",
                initial_sidebar_state="expanded"
            )
        except:
            # If it fails (e.g., not the first command), use the HTML approach
            pass

    def display_header(self):
        """Display the application header"""
        # Inject custom HTML to set the page title
        st.markdown(
            """
            <script>
                document.title = "Agentic API Forge";
                // Also set favicon
                var link = document.querySelector("link[rel*='icon']") || document.createElement('link');
                link.type = 'image/x-icon';
                link.rel = 'shortcut icon';
                link.href = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🔧</text></svg>';
                document.getElementsByTagName('head')[0].appendChild(link);
            </script>
            """,
            unsafe_allow_html=True
        )

        st.title("Agentic API Forge")
        st.subheader("Convert RAML to Python Code")
        st.write("Upload a RAML file and generate Python client, Flask API, and test code.")

    # In ui/streamlit_app.py, modify the get_user_inputs method:
    def get_user_inputs(self) -> Tuple:
        """
        Get user inputs from the Streamlit UI

        Returns:
            Tuple containing:
                - uploaded_file: The uploaded RAML file
                - generate_client: Boolean indicating whether to generate Python client code
                - generate_flask: Boolean indicating whether to generate Flask API code
                - generate_tests: Boolean indicating whether to generate test code
                - base_dir: Base directory for resolving includes
        """
        st.header("Upload RAML File")
        uploaded_file = st.file_uploader("Choose a RAML file", type=["raml", "yaml", "yml"])

        # Set default base directory to current working directory
        import os
        default_base_dir = os.getcwd()

        # Add a field for the base directory
        base_dir = st.text_input("Base directory for !include directives", 
                                value=default_base_dir if uploaded_file else "")

        st.header("Generation Options")
        generate_client = st.checkbox("Generate Python Client", value=True)
        generate_flask = st.checkbox("Generate Flask API", value=True)
        generate_tests = st.checkbox("Generate Tests", value=True)

        return uploaded_file, generate_client, generate_flask, generate_tests, base_dir

    def display_results(
        self,
        results: Dict[str, Any],
        generate_client: bool,
        generate_flask: bool,
        generate_tests: bool,
    ):
        """
        Display the generated code

        Args:
            results: Dictionary containing generated code
            generate_client: Boolean indicating whether Python client code was requested
            generate_flask: Boolean indicating whether Flask API code was requested
            generate_tests: Boolean indicating whether test code was requested
        """
        st.header("Generated Code")

        # Check for overall errors
        if results.get("status") == "error":
            st.error(f"Error: {results.get('message', 'Unknown error')}")
            return

        # Display Python client code if requested
        if generate_client:
            st.subheader("Python Client Code")
            if results.get("client_status") == "error":
                st.error(
                    f"Error generating Python client code: {results.get('client_message', 'Unknown error')}"
                )
            elif results.get("client_code"):
                st.code(results["client_code"], language="python")
                self._add_download_button(
                    results["client_code"], "python_client.py", "Download Python Client"
                )
            else:
                st.info("No Python client code was generated.")

        # Display Flask API code if requested
        if generate_flask:
            st.subheader("Flask API Code")
            if results.get("flask_status") == "error":
                st.error(
                    f"Error generating Flask API code: {results.get('flask_message', 'Unknown error')}"
                )
            elif results.get("flask_code"):
                st.code(results["flask_code"], language="python")
                self._add_download_button(
                    results["flask_code"], "flask_api.py", "Download Flask API"
                )
            else:
                st.info("No Flask API code was generated.")

        # Display test code if requested
        if generate_tests:
            st.subheader("Test Code")
            if results.get("test_status") == "error":
                st.error(
                    f"Error generating test code: {results.get('test_message', 'Unknown error')}"
                )
            elif results.get("test_code"):
                st.code(results["test_code"], language="python")
                self._add_download_button(
                    results["test_code"], "tests.py", "Download Tests"
                )
            else:
                st.info("No test code was generated.")

    def _add_download_button(self, code: str, filename: str, button_text: str):
        """
        Add a download button for code

        Args:
            code: The code to download
            filename: The filename for the downloaded file
            button_text: The text to display on the button
        """
        st.download_button(
            label=button_text, data=code, file_name=filename, mime="text/plain"
        )

    def display_help(self):
        """Display help information"""
        with st.expander("Help & Information"):
            st.markdown(
                """
            ### About RAML Code Generator

            This tool generates code from RAML (RESTful API Modeling Language) specifications. It can generate:

            - **Python Client**: A Python client library for consuming the API
            - **Flask API**: A Flask implementation of the API
            - **Tests**: Pytest test cases for the API

            ### How to Use

            1. Upload a RAML file using the file uploader
            2. Select the types of code you want to generate
            3. Click the "Generate Code" button
            4. View and download the generated code

            ### RAML Format

            Your RAML file should follow the [RAML specification](https://raml.org/). Here's a simple example:

            ```yaml
            #%RAML 1.0
            title: Example API
            version: v1
            baseUri: https://api.example.com/{version}

            /users:
              get:
                description: Get all users
                responses:
                  200:
                    body:
                      application/json:
                        example: |
                          [
                            {"id": 1, "name": "John"},
                            {"id": 2, "name": "Jane"}
                          ]
              post:
                description: Create a new user
                body:
                  application/json:
                    example: |
                      {"name": "John"}
                responses:
                  201:
                    body:
                      application/json:
                        example: |
                          {"id": 3, "name": "John"}
            ```
            """
            )
