import json
from pathlib import Path

import streamlit as st
from streamlit_ace import st_ace

from src.schema_flow import extract_data_with_schema, generate_schema, get_schema_class
from src.ui_helpers import get_images_cached

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

PLACEHOLDER_SCHEMA = '''from pydantic import BaseModel
from typing import List, Optional

class Document(BaseModel):
    """Edit this schema or use 'Generate Schema' to create one automatically."""
    title: Optional[str] = None
    content: Optional[List[str]] = None
'''

# Initialize session state variables
# uploaded file
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
# page image objects
if "pages" not in st.session_state:
    st.session_state.pages = None
# generated/edited data schema
if "schema" not in st.session_state:
    st.session_state.schema = PLACEHOLDER_SCHEMA
# extracted (JSON) data
if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None
# selected pages indices
if "selected_pages" not in st.session_state:
    st.session_state.selected_pages = []

def toggle_page(idx):
    if idx in st.session_state.selected_pages:
        st.session_state.selected_pages.remove(idx)
    else:
        st.session_state.selected_pages.append(idx)

# Welcome message first, then title
st.markdown("# 🤖 Welcome!")
st.info(WELCOME_MESSAGE, icon="🎯")

st.divider()

# Title
st.title("Schema-based data extraction from documents")

# File uploader
uploaded_file = st.file_uploader("Upload a file", type=["pdf"])

if uploaded_file is not None and st.session_state.uploaded_file != uploaded_file:
    st.session_state.uploaded_file = uploaded_file
    # Save the uploaded file to a temporary location
    tmp_path = Path("tmp") / uploaded_file.name
    tmp_path.parent.mkdir(exist_ok=True)
    with open(tmp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    pages = get_images_cached(tmp_path)
    # unlink the temporary file
    tmp_path.unlink()

    # Limit pages to first 10
    if len(pages) > 10:
        st.warning(f"Document has {len(pages)} pages. Only the first 10 pages will be processed.")
        pages = pages[:10]

    st.session_state.pages = pages
    st.session_state.schemas = None  # Reset schema
    st.session_state.extracted_data = None  # Reset extracted data

if st.session_state.pages is not None:
    st.write("## Page Selection")
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.write(f"Total pages: {len(st.session_state.pages)}")
        if st.checkbox("Select all pages", key="select_all"):
            st.session_state.selected_pages = list(range(len(st.session_state.pages)))
        else:
            # Only clear if it was previously all selected
            if len(st.session_state.selected_pages) == len(st.session_state.pages):
                st.session_state.selected_pages = []
        
    with col1:
        # Create a grid layout for page selection
        cols = st.columns(4)
        for idx, page in enumerate(st.session_state.pages):
            with cols[idx % 4]:
                st.image(page, caption=f"Page {idx + 1}", use_column_width=True)
                if st.checkbox(
                    f"Include page {idx + 1}",
                    value=idx in st.session_state.selected_pages,
                    key=f"page_{idx}",
                    on_change=lambda i=idx: toggle_page(i)
                ):
                    if idx not in st.session_state.selected_pages:
                        st.session_state.selected_pages.append(idx)
                else:
                    if idx in st.session_state.selected_pages:
                        st.session_state.selected_pages.remove(idx)

    n_selected = len(st.session_state.selected_pages)
    st.write(f"Selected pages: {n_selected}")

    # Show schema section
    st.write("## Schema Definition")
    st.write("You can either edit the schema directly or generate one from selected pages.")
    
    # Generate schema first
    if n_selected > 0 and st.button("Generate Schema", key="generate_schema_button"):
        selected_pages = [st.session_state.pages[i] for i in st.session_state.selected_pages]
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
