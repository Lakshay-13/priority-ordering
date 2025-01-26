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
        "Need": ["Task 1", "Task 2", "Task 3", "Task 4"],
        "Time": ["Task 1", "Task 2", "Task 3", "Task 4"],
        "Skill": ["Task 1", "Task 2", "Task 3", "Task 4"],
        "Worth": ["Task 1", "Task 2", "Task 3", "Task 4"],
        "Deadline": ["Task 1", "Task 2", "Task 3", "Task 4"]
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
for category, blocks in categories.items():
    if f"{category}_order" not in st.session_state:
        st.session_state[f"{category}_order"] = blocks

# Title
st.title("Priority Manager")
st.write("Drag and drop the blocks below to reorder your priorities for each category.")

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

# Render sorting tables
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
