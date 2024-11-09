import streamlit as st
from utils import conversations
from functools import partial
from ui import prints
from utils import github

def render_sidebar():
    """
    Renders a sidebar of active repos that are being queried
    """
    with st.sidebar:
        st.markdown(":blue[Code Insights 👓]")
        st.button("+ New Conversation 🔊", on_click=conversations.start_new_convo, use_container_width=True)  
        st.markdown("---")
        st.markdown(":blue[Recent Conversations 💬]")
        with st.container():
            for idx, convos in enumerate(st.session_state.global_messages):  # Reverse the ordering of convos from most recent
                chat_col, delete_col = st.columns([0.9, 0.1])

                with chat_col:
                    update_callback = partial(conversations.update_active_convo, idx)  # makes callbacks dynamic
                    repo_url = convos.get("repo")
                    if repo_url is not None:
                        repo_display_name = convos.get("repo_display_name")
                        if repo_display_name == repo_url:  # If user chose not to set a repo display name
                            st.button(f"{idx+1}. {repo_url} 📚 ", on_click=update_callback, use_container_width=True, key=f"convo_{idx}")
                        else:
                            st.button(f"{idx+1}. {repo_display_name} 📖", on_click=update_callback, use_container_width=True, key=f"convo_{idx}")
                
                        with delete_col:
                            delete_convo_callback = partial(conversations.delete_convo, idx)
                            st.button(f"🗑️", on_click=delete_convo_callback, key=f"delete_{idx}")


def render_conversations():
    """
    Renders chat messages in chat
    """
    for message in st.session_state.global_messages[conversations.get_active_convo()]["messages"]:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.write(message["content"])


def render_new_conversation():
    """
    Handles if there is a request to start a new conversation and reanimates the page accordingly
    """
    if st.session_state.animation.get("new_convo"):
        conversations.setup_repo_convo()
        st.session_state.animation["new_convo"] = False


def get_user_chat_input():
    """
    Gets user's chat inputs.
    Returns user inputs as a dictionary of user role and the message content 
    """
    if prompt := st.chat_input("Type your message", key=f"input_{st.session_state.chat_counter}"):
        # Save user input
        prompt_msg = {"role": "user", "content": prompt}
        # Increment input counter to keep buttons unique
        st.session_state.chat_counter += 1
        return prompt_msg
    return {}


def ask_for_repo_details():
    """
    Ask for both the repository URL and display name in a single container.
    The display name is optional and will default to the URL if not provided.
    """
    st.markdown("""
    ## Setup Your Repository Information

    To proceed, please provide the **Repository URL** and an optional **Display Name** for the repository. 
    The **Display Name** will be used when referencing the repository in the interface. If you don't provide a display name, 
    it will default to the repository URL.

    Make sure the URL points to a valid GitHub repository, and feel free to rename it as needed for easier reference.
    """)

    if 'repo_url' not in st.session_state:
        st.session_state.repo_url = ""  # Initialize if not present
    if 'repo_name' not in st.session_state:
        st.session_state.repo_name = ""  # Initialize if not present

    # Create two input fields side by side
    col1, col2 = st.columns([2, 3])  # Adjust column ratios for layout

    with col1:
        # Repo display name input (with default as empty)
        repo_name = st.text_input("Enter Repository Display Name",
                                  value=st.session_state.repo_name,
                                  key="repo_name_input")
        st.session_state.chat_counter += 1
        st.session_state.repo_name = repo_name  # Persist name - since <enter>ing value reload page

    with col2:
        # Repo URL input
        repo_url = st.text_input("Enter Repository URL", 
                                 value=st.session_state.repo_url,
                                 key="repo_url_input")
        st.session_state.chat_counter += 1
        st.session_state.repo_url = repo_url   # Persist URL - since <enter>ing value reloads the page

        # Initialize is_valid to False
        is_valid = False
        if repo_url.strip():
            # Validate the repo URL
            is_valid = github.is_valid_github_repo(repo_url)
            # Show a tick or cross based on the validity of the URL
            if is_valid:
                st.markdown("✅ Valid Github Repo URL")
            else:
                st.markdown("❌ Invalid GitHub Repo URL")
        else:
            st.markdown("❌ The GitHub repository URL cannot be empty.")

    if repo_url.strip() and is_valid:  # Only proceed if the URL is valid
        # Default repo name to repo URL if not provided
        if not repo_name.strip():
            repo_name = repo_url

        # Reset on success
        st.session_state.repo_name = ""
        st.session_state.repo_url = ""
        return repo_url, repo_name
    else:
        # Provide a clear message to the user if repo_url is empty or invalid
        if not repo_url:
            st.error("Please enter a valid GitHub repository URL.")
        elif not is_valid:
            st.error("The provided GitHub repository URL is invalid. Please correct it.")
        return "", ""  # Return empty strings if no valid input is provided


class DownloadButton():
    """
    Custom download button for downloading documents.
    Attaches Microsoft docx documents.
    """
    def __init__(self, label, data, file_name):
        self.label = label
        self.data = data
        self.file_name = file_name

    def render(self):
        st.download_button(label=self.label, 
                           data=self.data, 
                           file_name=self.file_name, 
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


class ConvoDLButton(DownloadButton):
    """
    Custom download buttons for downloading documents in Chat.
    Attaches Microsoft docx documents.
    """
    def __init__(self, data, file_name):
        super().__init__("Download Report 📜", data, file_name)


class SidebarDLButton(DownloadButton):
    """
    Custom download buttons for downloading documents in Sidebar.
    """
    def __init__(self, data, file_name):
        super().__init__("", data, file_name)

    def render(self):
        st.download_button(label=self.file_name,
                            data=self.data,
                            file_name=self.file_name,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


