import streamlit as st
from utils import conversations
from functools import partial
from ui import prints

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


def get_user_chat_input():
    """
    Gets user's chat inputs.
    Pretty prints their inputs via streaming to the chatbox for the first event loop.
    Returns user inputs as a dictionary of user role and the message content 
    """
    if prompt := st.chat_input("Type your message", key=f"input_{st.session_state.chat_counter}"):
        # Save user input
        prompt_msg = {"role": "user", "content": prompt}
        st.chat_message("user").write_stream(prints.fake_print_stream(prompt))

        # Increment input counter to keep things unique
        st.session_state.chat_counter += 1
        return prompt_msg
    return {}


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


