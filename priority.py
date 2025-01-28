import streamlit as st
from streamlit_sortables import sort_items
from google.cloud import storage
from google.oauth2.service_account import Credentials
import json
import os
os.write(1, b'Application started \n')

# Load credentials from Streamlit secrets
credentials_dict = dict(st.secrets["gcp"])
# Create credentials object from the dict
gcs_credentials = Credentials.from_service_account_info(credentials_dict)
client = storage.Client(credentials=gcs_credentials)

# Initial configuration
st.set_page_config(page_title="Priority Manager v1.1", layout="wide")

def get_gcs_client():
    """
    Initialize Google Cloud Storage client.
    """
    return client

def normalize_user_id(user_id):
    """
    Normalize the user ID by converting to lowercase and replacing spaces with underscores.
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
                {"Need": f"Task {i+1}", "Time": f"Task {i+1}", "Skill": f"Task {i+1}", "Worth": f"Task {i+1}", "Deadline": f"Task {i+1}"}
                for i in range(4)
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
                items=blocks,
                direction="vertical",
                key=f"sortable_{category}",
            )
            # Update the category with the new order
            st.session_state.categories[category] = new_order

def manage_tasks():
    """
    Submenu for managing task names.
    """
    st.subheader("Manage Tasks")
    tasks = st.session_state.tasks_to_edit.copy()

    with st.form(key='tasks_form'):
        # Display existing tasks and edit/remove options
        tasks_to_remove = []
        for idx, task in enumerate(tasks):
            col1, col2 = st.columns([4, 1])
            with col1:
                updated_task = st.text_input(f"Edit Task {idx + 1}", task, key=f"edit_task_{idx}")
                tasks[idx] = updated_task
            with col2:
                remove = st.checkbox("Remove", key=f"remove_{idx}")
                if remove:
                    tasks_to_remove.append(idx)

        # Remove tasks marked for removal
        for idx in sorted(tasks_to_remove, reverse=True):
            del tasks[idx]

        # Add a new task
        new_task = st.text_input("Add a New Task:", key="new_task_form")
        if new_task:
            tasks.append(new_task)

        submitted = st.form_submit_button("Update Tasks")

    if submitted:
        st.session_state.tasks_to_edit = tasks
        # Update the categories with the new tasks but keep the existing orders
        rebuild_sheet_data_with_updated_tasks()
        st.success("Tasks updated.")
        st.session_state.manage_tasks_view = False  # Close the task management view immediately

def rebuild_sheet_data_with_updated_tasks():
    """
    Rebuilds the sheet_data with the updated tasks, maintaining the order in each category.
    """
    # Get the current categories and their orders
    categories = st.session_state.categories
    tasks = st.session_state.tasks_to_edit
    # Ensure all tasks are included in each category
    for category in categories:
        current_tasks = categories[category]
        # Remove tasks that no longer exist
        categories[category] = [task for task in current_tasks if task in tasks]
        # Add new tasks at the end
        for task in tasks:
            if task not in categories[category]:
                categories[category].append(task)
    # Build new sheet_data
    data_to_save = []
    max_length = max(len(blocks) for blocks in categories.values())
    for i in range(max_length):
        row = {}
        for category, blocks in categories.items():
            row[category] = blocks[i] if i < len(blocks) else ""
        data_to_save.append(row)
    # Update st.session_state.sheet_data
    st.session_state.sheet_data = data_to_save
    # Save the data
    save_user_data(st.session_state.user_id, data_to_save)

# Initialize session state variables
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "manage_tasks_view" not in st.session_state:
    st.session_state.manage_tasks_view = False
if "tasks_to_edit" not in st.session_state:
    st.session_state.tasks_to_edit = []
if "categories" not in st.session_state:
    st.session_state.categories = {}
if "sheet_data" not in st.session_state:
    st.session_state.sheet_data = []

# Title
st.title("Priority Manager v1.1")

# Instructions
st.markdown("""
### Instructions:
1. **Reordering Tasks:** The first re-order in any session will refresh the page and may not apply the change. This is normal. Subsequent changes will work as expected.
2. **Saving Changes:** After making your changes, click the **Save Changes** button to save the order for your next login.
3. **Managing Tasks:** When adding or removing tasks, make all your changes, then click the **Update Tasks** button twice. Refresh the page to see the changes reflected.
""")

st.write("Enter your user ID and password to begin. If you're a new user, register below.")

# User ID and password input
user_id_input = st.text_input("Enter your User ID:")
password_input = st.text_input("Enter your Password:", type="password")
# Center the Login button
col1, col2, col3, col4, col5 = st.columns(5)
with col3:
    login_button = st.button("Login / Load Data")

if login_button:
    normalized_user_id = normalize_user_id(user_id_input)

    if verify_password(normalized_user_id, password_input):
        st.success("Login successful!")
        st.session_state.logged_in = True
        st.session_state.user_id = normalized_user_id
        st.session_state.sheet_data = load_user_data(normalized_user_id)
        # Initialize tasks_to_edit from sheet_data
        tasks_set = set()
        for row in st.session_state.sheet_data:
            tasks_set.update(row.values())
        tasks = sorted(tasks_set)
        st.session_state.tasks_to_edit = tasks
        # Initialize categories
        categories = {
            "Need": [row["Need"] for row in st.session_state.sheet_data],
            "Time": [row["Time"] for row in st.session_state.sheet_data],
            "Skill": [row["Skill"] for row in st.session_state.sheet_data],
            "Worth": [row["Worth"] for row in st.session_state.sheet_data],
            "Deadline": [row["Deadline"] for row in st.session_state.sheet_data],
        }
        st.session_state.categories = categories
    else:
        st.error("Invalid username or password.")
        st.session_state.logged_in = False

# Check if the user is logged in
if st.session_state.logged_in:
    # Use the categories from session state
    categories = st.session_state.categories

    # Drag-and-drop UI
    st.write("Drag and drop the blocks below to reorder your priorities for each category.")
    render_sorting_tables(categories)

    # Center the Save Changes button
    col1, col2, col3, col4, col5 = st.columns(5)
    with col2:
        if st.button("Save Changes", key="save_button"):
            # Build sheet_data from categories
            data_to_save = []
            max_length = max(len(blocks) for blocks in categories.values())
            for i in range(max_length):
                row = {}
                for category, blocks in categories.items():
                    row[category] = blocks[i] if i < len(blocks) else ""
                data_to_save.append(row)
            # Update session state and save data
            st.session_state.sheet_data = data_to_save
            save_user_data(st.session_state.user_id, data_to_save)
            st.success("Changes saved successfully!", icon="✅")

    with col4:
        if st.button("Manage Tasks", key="manage_tasks_button"):
            st.session_state.manage_tasks_view = True

    if st.session_state.manage_tasks_view:
        st.write("---")
        manage_tasks()

# Registration form
if not st.session_state.logged_in:
    st.write("---")
    st.subheader("New User Registration")
    new_user_id = st.text_input("Choose a Username:")
    new_password = st.text_input("Choose a Password:", type="password")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col3:
        register_button = st.button("Register")

    if register_button:
        normalized_new_user_id = normalize_user_id(new_user_id)
        if normalized_new_user_id == "username":
            st.error("'username' is not allowed as a username. Please choose a different one.")
        else:
            save_password(normalized_new_user_id, new_password)