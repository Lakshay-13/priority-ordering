import streamlit as st
import json
from pathlib import Path
from streamlit_sortables import sort_items

# File to store the priority orders
DATA_FILE = Path("priority_orders.json")

# Load data from JSON file
def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    return {
        "Need": ["Pavlos' Job", "Education Business", "E Consulting", "I Consulting"],
        "Time": ["Pavlos' Job", "Education Business", "E Consulting", "I Consulting"],
        "Skill": ["Pavlos' Job", "Education Business", "E Consulting", "I Consulting"],
        "Worth": ["Pavlos' Job", "Education Business", "E Consulting", "I Consulting"],
        "Deadline": ["Pavlos' Job", "Education Business", "E Consulting", "I Consulting"]
    }

# Save data to JSON file
def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file)

# Load initial data
categories = load_data()

# Initial configuration
st.set_page_config(page_title="Priority Manager", layout="wide")

# Initialize session state for category order
if "global_order" not in st.session_state:
    st.session_state["global_order"] = categories["Need"]

for category, blocks in categories.items():
    if f"{category}_order" not in st.session_state:
        st.session_state[f"{category}_order"] = blocks

# Title
st.title("Priority Manager")
st.write("Drag and drop the blocks below to reorder your priorities for each category.")

# Function to render a single global editable section
def render_global_editable_section():
    with st.expander("Edit Items Globally"):
        items = st.session_state["global_order"]
        edited_items = []

        # Display items with edit and delete options
        for i, item in enumerate(items):
            cols = st.columns([8, 1, 1])
            edited_item = cols[0].text_input(f"Item {i+1}", item, key=f"global_item_{i}")
            if cols[1].button("➖", key=f"remove_global_{i}"):
                continue  # Skip adding this item
            edited_items.append(edited_item)

        # Add new item option
        if st.button("➕ Add item", key="add_global"):
            edited_items.append("New Item")

        # Update session state and propagate to all categories
        st.session_state["global_order"] = edited_items
        for category in categories.keys():
            st.session_state[f"{category}_order"] = edited_items

# Render sorting tables in a grid
def render_sorting_tables():
    col1, col2, col3 = st.columns(3)
    columns = [col1, col2, col3]

    for i, (category, blocks) in enumerate(categories.items()):
        with columns[i % 3]:
            st.subheader(category)
            new_order = sort_items(
                items=st.session_state[f"{category}_order"],
                direction="vertical",
                key=f"sortable_{category}",
            )
            st.session_state[f"{category}_order"] = new_order
            categories[category] = new_order

# Render global editable section and sorting tables
render_global_editable_section()
render_sorting_tables()

# Save updated data to JSON
if st.button("Save Changes", key="save_button"):
    save_data(categories)
    st.success("Changes saved successfully!", icon="✅")

# Center the save button
st.markdown(
    "<style>.stButton button { display: block; margin: 0 auto; }</style>",
    unsafe_allow_html=True
)