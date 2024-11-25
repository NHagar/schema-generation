import json

import streamlit as st
from streamlit_ace import st_ace

from components.files import file_uploader, page_selector
from components.schema_flow import (
    extract_data_with_schema,
    generate_schema,
    get_schema_class,
)
from components.state import initialize_state

WELCOME_MESSAGE = """
This app uses AI to help you extract structured data from documents. Here's how it works:

1. **Upload a document** - Supports PDF files (max 10 pages)
2. **Select pages** - Choose which pages you want to process
3. **Define your schema** - You have two options:
   - Edit the default schema directly in the code editor
   - Click 'Generate Schema' to automatically create one based on your selected pages
4. **Extract data** - The app will process your document according to the schema
5. **Download results** - Get your structured data as a JSON file

The schema defines what data to extract and how to structure it. It uses Python's Pydantic library for data validation.

📚 Want to learn more? Check out the [detailed blog post](https://your-blog-post-url.com) about the technology behind this app.
"""

# Initialize session state variables
initialize_state()

# Welcome message first, then title
st.markdown("# 🤖 Welcome!")
st.info(WELCOME_MESSAGE, icon="🎯")

st.divider()

# Title
st.title("Schema-based data extraction from documents")

# File uploader
file_uploader()

if st.session_state.pages is not None:
    n_selected = page_selector()

    # Show schema section
    st.write("## Schema Definition")
    st.write(
        "You can either edit the schema directly or generate one from selected pages."
    )

    # Generate schema first
    if n_selected > 0 and st.button("Generate Schema", key="generate_schema_button"):
        selected_pages = [
            st.session_state.pages[i] for i in st.session_state.selected_pages
        ]
        schema = generate_schema(selected_pages)
        st.session_state.schema = schema
        # Force a rerun to update the ace editor
        st.rerun()

    # Then show the editor with the current schema
    edited_schema = st_ace(
        value=st.session_state.schema,
        language="python",
        key="schema_editor",
        height=300,
        theme="monokai",
    )

    if edited_schema != st.session_state.schema:
        st.session_state.schema = edited_schema

    # Extract data button
    if st.button("Extract Data", key="extract_data_button", disabled=n_selected == 0):
        schema_code = st.session_state.schema
        if schema_code is not None:
            schema_class, _ = get_schema_class(schema_code)
            # Extract data
            selected_pages = [
                st.session_state.pages[i] for i in st.session_state.selected_pages
            ]
            data = extract_data_with_schema(selected_pages, schema_class)
            st.session_state.extracted_data = data
            st.success("Data extracted successfully.")
        else:
            st.error("Please generate or provide a schema first.")

    # If data has been extracted, allow user to download it as JSON
    if st.session_state.extracted_data is not None:
        data = st.session_state.extracted_data
        json_data = json.dumps(data, indent=2)
        st.download_button(
            label="Download Extracted Data",
            data=json_data,
            file_name="data.json",
            mime="application/json",
        )
