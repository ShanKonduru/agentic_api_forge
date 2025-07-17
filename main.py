# main.py
import streamlit as st
from ui.streamlit_app import StreamlitUI
from agents.coordinator_agent import CoordinatorAgent
import os

# Set page configuration at the very beginning
st.set_page_config(
    page_title="Agentic API Forge",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application entry point"""
    # Initialize UI
    ui = StreamlitUI()
    ui.display_header()

    # Get user inputs
    uploaded_file, generate_client, generate_flask, generate_tests, base_dir = ui.get_user_inputs()

    # Process if we have a file and at least one generation option
    if uploaded_file is not None and any([generate_client, generate_flask, generate_tests]):
        if st.button("Generate Code"):
            with st.spinner("Processing RAML and generating code..."):
                # Read RAML content
                raml_content = uploaded_file.getvalue().decode("utf-8")

                # Use current directory if base_dir is empty
                if not base_dir:
                    base_dir = os.getcwd()

                # Initialize coordinator agent
                coordinator = CoordinatorAgent()

                try:
                    # Generate code
                    results = coordinator.run(
                        raml_content=raml_content,
                        base_dir=base_dir,
                        generate_client=generate_client,
                        generate_flask=generate_flask,
                        generate_tests=generate_tests
                    )

                    # Display results
                    ui.display_results(results, generate_client, generate_flask, generate_tests)

                except Exception as e:
                    st.error(f"Error during code generation: {str(e)}")
                    st.error("Please check that your RAML file is valid and try again.")

# Run the app
if __name__ == "__main__":
    main()