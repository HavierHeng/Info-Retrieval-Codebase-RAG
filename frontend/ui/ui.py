import streamlit as st
from utils import conversations
from functools import partial
from utils import git_helper

def sidebar_callback(convo):
    """
    Toggle sidebar display value for a certain conversation
    """
    convo["sidebar_details"] = not convo["sidebar_details"]

def render_sidebar():
    """
    Renders a sidebar of active repos that are being queried
    """
    with st.sidebar:
        st.markdown(":blue[Code Insights 👓]")
        st.button("New Conversation 🔊", on_click=conversations.start_new_convo, use_container_width=True, icon=":material/add_box:")  
        st.markdown("---")
        st.markdown(":blue[Recent Conversations 💬]")
        with st.container():
            for idx, convos in enumerate(st.session_state.global_messages): 
                chat_col, more_info_col, delete_col = st.columns([0.7, 0.15, 0.15])

                with chat_col:
                    update_callback = partial(conversations.update_active_convo, idx)  # makes callbacks dynamic
                    repo_location = convos.get("repo")
                    if repo_location is not None:
                        repo_display_name = convos.get("repo_display_name")
                        repo_branch = convos.get("repo_branch")
                        repo_commit_sha = convos.get("repo_commit_sha")
                        repo_owner = convos.get("repo_owner")
                        repo_pull_date = convos.get("pull_date")
                        repo_path = convos.get("repo_path")
                        is_remote = convos.get("is_remote")

                        st.button(f"{repo_display_name}",
                                  on_click=update_callback, 
                                  use_container_width=True,
                                  key=f"convo_{idx}",
                                  icon=":material/code:")

                        with more_info_col:
                            # Button to toggle info
                            more_info_callback = partial(sidebar_callback, convos)
                            st.button("",
                                      on_click = more_info_callback, 
                                      use_container_width=True,
                                      key = f"more_info_{idx}",
                                      help = "More Repository Details",
                                      icon=":material/arrow_drop_down:")
                        with delete_col:
                            delete_convo_callback = partial(conversations.delete_convo, idx, is_remote)
                            st.button(f"🗑️", on_click=delete_convo_callback, use_container_width=True, key=f"delete_{idx}")

                        if convos.get("sidebar_details"):
                            # if button pressed for this idx
                            repo_details = ["**Detailed Information:**  "]
                            
                            if is_remote:
                                repo_details.extend([f":gray[Owner: {repo_owner}]  ", 
                                                     f":gray[Location: {repo_location}]  ", 
                                                     f":gray[Local/Remote: {"Remote" if is_remote else "Local"}]  ",
                                                     f":gray[Active Branch: {repo_branch}]  ", 
                                                     f":gray[Commit Hash: {repo_commit_sha}]  ", 
                                                     f":gray[Local Path: {repo_path}]  ", 
                                                     f":gray[Date: {repo_pull_date.strftime('%d %b %Y %X')}]  "])
                            elif not is_remote:
                                repo_details.extend([ f":gray[Location: {repo_location}]  ", 
                                                     f":gray[Local/Remote: {"Remote" if is_remote else "Local"}]  ",
                                                     f":gray[Active Branch: {repo_branch}]  ", 
                                                     f":gray[Commit Hash: {repo_commit_sha}]  ", 
                                                     f":gray[Date: {repo_pull_date.strftime('%d %b %Y %X')}]  "])
                            else:
                                repo_details.append(":gray[No details available...]  ")

                            repo_details = "\n".join(repo_details)
                            st.markdown(repo_details)


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
    curr_convo = conversations.get_active_convo()
    if st.session_state.animation.get("new_convo"): 
        is_remote_toggle = st.session_state.is_remote_toggle
        repo_url, repo_name = ask_for_repo_details()  

        if repo_url and repo_name:
            # Store the information in session state
            st.session_state.global_messages[curr_convo]["repo"] = repo_url
            st.session_state.global_messages[curr_convo]["repo_display_name"] = repo_name
            st.session_state.global_messages[curr_convo]["is_remote"] = is_remote_toggle
            # Exit animation for new conversation
            st.session_state.animation["new_convo"] = False


def render_process_repository():
    """
    Handles if current repo has been successfully processed - i.e cloned and indexed into RAG database.
    Sets a processed flag if succeeded.
    If it is not, it will reattempt again through the main loop. 
    This is in the event user interrupts the processing stage due to impatience.
    """
    curr_convo = conversations.get_active_convo()
    if st.session_state.animation.get("process_repo"):

        # Interruptable here - but flag won't be set until process_repository() is done
        if st.session_state.global_messages[curr_convo]["is_remote"]:  # Remote
            st.session_state.global_messages[curr_convo]["processed"] = conversations.process_remote_repository()

        if not st.session_state.global_messages[curr_convo]["is_remote"]:  # Local
            st.session_state.global_messages[curr_convo]["processed"] = conversations.process_local_repository()

        # Finished - can set flag
        st.session_state.animation["process_repo"] = False

        # Set up first bit of code convo for user query
        conversations.start_code_convo(curr_convo)  # Regenerate messages


SETUP_REPO_INFO = """
## Setup Your Repository Information

To proceed, please provide the **Repository Location (Path or URL)** and an optional **Display Name** for the repository. 
The **Display Name** will be used when referencing the repository in the interface. If you don't provide a display name, 
it will default to the repository root directory (for local) or repository URL (for remote).

Make sure the URL points to a valid GitHub repository, and feel free to rename it as needed for easier reference.
"""

def ask_for_repo_details():
    """
    Ask for both the repository details (local or remote) and display name in a single container.
    The display name is optional and will default to the name of the root directory (for local repos) 
    or the repo name from the URL (for remote repos) if not provided.
    """
    st.markdown(SETUP_REPO_INFO)

    repo_url = ""
    repo_path = ""

    # Toggle between remote or local repository type
    options = [":material/sync_saved_locally: Local", ":material/cloud_download: Remote"]
    repo_type = st.radio("Choose Repository Type", 
                         options,
                         captions=["Use a local Git repository, such as your own codebase!", "Clone from Github, good for learning about remote codebases."],
                         index = 1)
    if repo_type:
        if repo_type == options[0]:  # Local selected
            st.session_state["is_remote_toggle"] = False
        if repo_type == options[1]:  # Remote selected
            st.session_state["is_remote_toggle"] = True

    is_remote = st.session_state["is_remote_toggle"]

    with st.form("Repository Details", border=False):
        # Create two input fields side by side
        col1, col2 = st.columns([2, 3])  # Adjust column ratios for layout
        with col1:
            # Repo display name input (with default as empty)
            repo_name = st.text_input("Enter Repository Display Name", key="repo_name")

        with col2:
            if is_remote:
                # Repo URL input for remote repositories
                repo_url = st.text_input("Enter Repository URL", key="repo_url")
                # Initialize is_valid to False
                is_valid = False 

                if repo_url and repo_url.strip():
                    # Validate the repo URL against GitHub
                    is_valid = git_helper.is_valid_github_repo(repo_url)
                    # Show a tick or cross based on the validity of the URL
                    if is_valid:
                        st.markdown("✅ Valid Github Repo URL")
                    else:
                        st.markdown("❌ Invalid GitHub Repo URL")
                else:
                    st.markdown("❌ The GitHub repository URL cannot be empty.")
                    
            else:
                # Repo Path input for local repositories
                repo_path = st.text_input("Enter Repository Path", key="repo_path")

                # Initialize is_valid to False
                is_valid = False

                if repo_path and repo_path.strip():
                    # Validate the repo URL (Local: Path to Git repository)
                    is_valid = git_helper.is_valid_local_git_repo(repo_path)
                    # Show a tick or cross based on the validity of the path
                    if is_valid:
                        st.markdown("✅ Valid Git Path")
                    else:
                        st.markdown("❌ Invalid Git Path")
                else:
                    st.markdown("❌ The Git Path cannot be empty.")
        
        submitted = st.form_submit_button("Submit", icon=":material/send:")
        
        if submitted:
            if is_remote:
                # Remote: If valid URL and provided, process the remote repo
                if repo_url.strip() and is_valid:
                    # Default repo name to repo name inferred from URL if not provided
                    if not repo_name.strip():
                        _, repo_name = git_helper.get_repo_owner_name_from_url(repo_url)

                    # Reset on success
                    # st.session_state.repo_name = ""
                    # st.session_state.repo_url = ""
                    return repo_url, repo_name
                else:
                    # Provide a clear message to the user if repo_url is empty or invalid
                    if not repo_url:
                        st.error("Please enter a valid GitHub repository URL.")
                    elif not is_valid:
                        st.error("The provided GitHub repository URL is invalid. Please correct it.")
                    return "", ""  # Return empty strings if no valid input is provided
            else:
                # Local: If valid path and provided, process the local repo
                if repo_path.strip() and is_valid:
                    # Default repo name to repo root dir if not provided
                    if not repo_name.strip():
                        repo_name = git_helper.get_local_repo_root_dir(repo_path)

                    # Reset on success
                    # TODO: Fix 
                    # st.session_state.repo_name = ""
                    # st.session_state.repo_path = ""
                    return repo_path, repo_name
                else:
                    # Provide a clear message to the user if repo_path is empty or invalid
                    if not repo_path:
                        st.error("Please enter a valid Git Path.")
                    elif not is_valid:
                        st.error("The provided Git Path is invalid. Please correct it.")
                    return "", ""  # Return empty strings if no valid input is provided

    return "", ""


def get_user_chat_input():
    """
    Gets user's chat inputs.
    Returns user inputs as a dictionary of user role and the message content 
    """

    # Input Box key has to be shared across states - else values will be lost between transitions
    if prompt := st.chat_input("Type your message", key="input_box"):
        # Save user input
        prompt_msg = {"role": "user", "content": prompt}
        # Increment input counter to keep buttons unique
        return prompt_msg
    return None 

def display_clone_progress():
    """
    Display the current GitPython clone progress bar and status in Streamlit.
    Currently unused due to GitPython progress issues.
    """
    progress = st.session_state.get("git", {}).get("clone_progress", 0.0)
    message = st.session_state.get("git", {}).get("message", "Initializing clone...")
    curr_op = st.session_state.get("git", {}).get("curr_op", "")
    
    st.write(f"Operation: {curr_op}")
    st.write(f"Message: {message}")
    
    # Display Streamlit progress bar
    st.progress(progress, text=f"{curr_op}: {message}")

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


