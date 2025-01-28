import streamlit as st
from streamlit_sortables import sort_items
from google.cloud import storage
from google.oauth2.service_account import Credentials
import json

# Load credentials from Streamlit secrets
credentials_dict = dict(st.secrets["gcp"])
# Create credentials object from the dict
gcs_credentials = Credentials.from_service_account_info(credentials_dict)
client = storage.Client(credentials=gcs_credentials)

# Initial configuration
st.set_page_config(page_title="Priority Manager v1.0", layout="wide")

def get_gcs_client():
    """
    Initialize Google Cloud Storage client.
    """
    return client

def normalize_user_id(user_id):
    """
    Normalize the user ID by converting to lowercase and replacing spaces or underscores with underscores.
    """
    return user_id.strip().lower().replace(" ", "_")

def load_user_data(user_id):
    """
    Load data for the specific user from GCS.
    """
    client = get_gcs_client()
    bucket_name = "priority-queue-13"  # Your bucket name
    file_path = f"{user_id}.json"  # JSON file for the user
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_path)

    try:
        if blob.exists():
            # File exists, load its content
            return json.loads(blob.download_as_text())
        else:
            # File doesn't exist, initialize with default data
            data = [
                {"Need": "Task 1", "Time": "Task 1", "Skill": "Task 1", "Worth": "Task 1", "Deadline": "Task 1"},
                {"Need": "Task 2", "Time": "Task 2", "Skill": "Task 2", "Worth": "Task 2", "Deadline": "Task 2"},
                {"Need": "Task 3", "Time": "Task 3", "Skill": "Task 3", "Worth": "Task 3", "Deadline": "Task 3"},
                {"Need": "Task 4", "Time": "Task 4", "Skill": "Task 4", "Worth": "Task 4", "Deadline": "Task 4"},
            ]
            save_user_data(user_id, data)
            return data
    except Exception as e:
        # Log the error
        st.error(f"Error loading user data: {e}")
        return []

def save_user_data(user_id, data):
    """
    Save data for the specific user to GCS, overwriting any existing file for the same user ID.
    """
    client = get_gcs_client()
    bucket_name = "priority-queue-13"  # Your bucket name
    file_path = f"{user_id}.json"
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_path)

    try:
        # Save the JSON data to GCS
        blob.upload_from_string(json.dumps(data), content_type="application/json")
    except Exception as e:
        # Log the error
        st.error(f"Error saving user data: {e}")

def save_password(username, password):
    """
    Save the username and password to a passwords.json file in GCS.
    """
    client = get_gcs_client()
    bucket_name = "priority-queue-13"  # Your bucket name
    file_path = "passwords.json"
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_path)

    try:
        if blob.exists():
            passwords = json.loads(blob.download_as_text())
        else:
            passwords = {}

        if username in passwords:
            st.error("Username already exists. Choose a different username.")
        else:
            passwords[username] = password
            blob.upload_from_string(json.dumps(passwords), content_type="application/json")
            st.success("New user registered successfully!")
    except Exception as e:
        st.error(f"Error saving password: {e}")

def verify_password(username, password):
    """
    Verify the username and password from the passwords.json file in GCS.
    """
    client = get_gcs_client()
    bucket_name = "priority-queue-13"  # Your bucket name
    file_path = "passwords.json"
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_path)

    try:
        if blob.exists():
            passwords = json.loads(blob.download_as_text())
            return passwords.get(username) == password
        else:
            return False
    except Exception as e:
        st.error(f"Error verifying password: {e}")
        return False

def render_sorting_tables(categories):
    """
    Render the sorting tables in a grid layout.
    """
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

def manage_tasks():
    """
    Submenu for managing task names.
    """
    st.subheader("Manage Tasks")

    if "tasks" not in st.session_state:
        st.session_state["tasks"] = ["Task 1", "Task 2", "Task 3", "Task 4"]

    tasks = st.session_state["tasks"]

    # Add a new task
    new_task = st.text_input("Add a new task:")
    if st.button("Add Task"):
        if new_task and new_task not in tasks:
            tasks.append(new_task)
            st.success(f"Task '{new_task}' added successfully!")

    # Edit existing tasks
    for i, task in enumerate(tasks):
        col1, col2 = st.columns([4, 1])
        with col1:
            updated_task = st.text_input(f"Edit Task {i + 1}", task, key=f"edit_{i}")
            if updated_task != task:
                tasks[i] = updated_task
        with col2:
            if st.button("Remove", key=f"remove_{i}"):
                tasks.pop(i)
                st.success(f"Task '{task}' removed successfully!")
                break

    # Save tasks and replicate across categories
    if st.button("Save Tasks"):
        categories = {
            "Need": tasks[:],
            "Time": tasks[:],
            "Skill": tasks[:],
            "Worth": tasks[:],
            "Deadline": tasks[:],
        }
        for key, values in categories.items():
            st.session_state[f"{key}_order"] = values
        st.success("Tasks updated across all categories.")

# Title
st.title("Priority Manager")
st.write("Enter your user ID and password to begin. If you're a new user, register below.")

# User ID and password input
user_id_input = st.text_input("Enter your User ID:")
password_input = st.text_input("Enter your Password:", type="password")
login_button = st.button("Login / Load Data")

if login_button:
    normalized_user_id = normalize_user_id(user_id_input)

    if verify_password(normalized_user_id, password_input):
        st.success("Login successful!")
        st.session_state["user_id"] = normalized_user_id
        sheet_data = load_user_data(normalized_user_id)

        categories = {
            "Need": [row["Need"] for row in sheet_data],
            "Time": [row["Time"] for row in sheet_data],
            "Skill": [row["Skill"] for row in sheet_data],
            "Worth": [row["Worth"] for row in sheet_data],
            "Deadline": [row["Deadline"] for row in sheet_data],
        }

        # Initialize session state for category order
        for category, blocks in categories.items():
            if f"{category}_order" not in st.session_state:
                st.session_state[f"{category}_order"] = blocks

        # Drag-and-drop UI
        st.write("Drag and drop the blocks below to reorder your priorities for each category.")
        render_sorting_tables(categories)

        # Save updated data to Google Cloud Storage
        if st.button("Save Changes", key="save_button"):
            data_to_save = []
            max_length = max(len(blocks) for blocks in categories.values())
            for i in range(max_length):
                row = {}
                for category, blocks in categories.items():
                    row[category] = blocks[i] if i < len(blocks) else ""
                data_to_save.append(row)
            save_user_data(normalized_user_id, data_to_save)
            st.success("Changes saved successfully!", icon="✅")

        # Task management submenu
        manage_tasks()

        # Center the save button
        st.markdown(
            "<style>.stButton button { display: block; margin: 0 auto; }</style>",
            unsafe_allow_html=True
        )
    else:
        st.error("Invalid username or password.")

# Registration form
if "user_id" not in st.session_state:
    st.write("---")
    st.subheader("New User Registration")
    new_user_id = st.text_input("Choose a Username:")
    new_password = st.text_input("Choose a Password:", type="password")
    register_button = st.button("Register")

    if register_button:
        normalized_new_user_id = normalize_user_id(new_user_id)
        if normalized_new_user_id == "username":
            st.error("'username' is not allowed as a username. Please choose a different one.")
        else:
            save_password(normalized_new_user_id, new_password)