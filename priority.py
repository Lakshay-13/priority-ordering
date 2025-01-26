import streamlit as st
from streamlit_sortables import sort_items
from google.cloud import storage
import json

# Initialize Google Cloud Storage client
def get_gcs_client():
    return storage.Client()

# Function to load data for the specific user
def load_user_data(user_id):
    client = get_gcs_client()
    bucket_name = "streamlit-bucket"
    file_path = f"{user_id}.json"
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_path)

    if blob.exists():
        return json.loads(blob.download_as_text())
    else:
        # If file doesn't exist, initialize with default data
        data = [
            {"Need": "Task 1", "Time": "Task 1", "Skill": "Task 1", "Worth": "Task 1", "Deadline": "Task 1"},
            {"Need": "Task 2", "Time": "Task 2", "Skill": "Task 2", "Worth": "Task 2", "Deadline": "Task 2"},
            {"Need": "Task 3", "Time": "Task 3", "Skill": "Task 3", "Worth": "Task 3", "Deadline": "Task 3"},
            {"Need": "Task 4", "Time": "Task 4", "Skill": "Task 4", "Worth": "Task 4", "Deadline": "Task 4"},
        ]
        save_user_data(user_id, data)
        return data

# Function to save data for the specific user
def save_user_data(user_id, data):
    client = get_gcs_client()
    bucket_name = "streamlit-bucket"
    file_path = f"{user_id}.json"
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_path)

    # Save the JSON data to GCS
    blob.upload_from_string(json.dumps(data), content_type="application/json")

# User ID (simulating with session state for now)
if "user_id" not in st.session_state:
    st.session_state["user_id"] = st.text_input("Enter your User ID:", "default_user")

user_id = st.session_state["user_id"]

# Load initial data for the user
sheet_data = load_user_data(user_id)

categories = {
    "Need": [row["Need"] for row in sheet_data],
    "Time": [row["Time"] for row in sheet_data],
    "Skill": [row["Skill"] for row in sheet_data],
    "Worth": [row["Worth"] for row in sheet_data],
    "Deadline": [row["Deadline"] for row in sheet_data],
}

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

# Save updated data to Google Cloud Storage
if st.button("Save Changes", key="save_button"):
    data_to_save = []
    max_length = max(len(blocks) for blocks in categories.values())
    for i in range(max_length):
        row = {}
        for category, blocks in categories.items():
            row[category] = blocks[i] if i < len(blocks) else ""
        data_to_save.append(row)
    save_user_data(user_id, data_to_save)
    st.success("Changes saved successfully!", icon="✅")

# Center the save button
st.markdown(
    "<style>.stButton button { display: block; margin: 0 auto; }</style>",
    unsafe_allow_html=True
)
