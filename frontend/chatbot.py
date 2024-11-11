import streamlit as st
from ui import ui
from utils import conversations


# Initial page setup
st.set_page_config(page_title="Codebase Query Helper", page_icon="🤖💬", layout="centered")

def init_session_state():
    """
    Sets up global session state if not already set up.
    """
# Global messages stores every conversation and their messages to display/provide as context to LLM
    if "global_messages" not in st.session_state:
        st.session_state.global_messages = []

    # Chat counters maintain a unique ID per st.chat_input()
    if "chat_counter" not in st.session_state:
        st.session_state.chat_counter = 0

    # Animation Update states - since callbacks are not executed in order leading to weird behaviors
    # One solution is to set a state in a callback, then handle it in the main loop
    if "animation" not in st.session_state:
        st.session_state.animation = {
            "new_convo": False,
            "process_repo": False
        }

    # Git Clone Progress state - for rendering reasons
    if "git" not in st.session_state:
        st.session_state.git = {"clone_progress": 0,
                                "curr_op": "",
                                "message": ""
                                }

    # Active conversation index - just keeps track of which conversation user is currently sending data to/rendering
    if "active_convo_idx" not in st.session_state:
        # First conversation - i.e just opened chatbot
        # Need to create a new blank active convo idx, as well as convo
        conversations.start_new_convo()
    else:
        # Have index - so not first conversation
        # In event of no repo details, need to get from user
        conversations.setup_repo_convo()


def main():
    """
    Main loop for streamlit application
    """
    st.title("Codebase RAG Chatbot") 
    init_session_state()

    ui.render_sidebar()
    ui.render_new_conversation()
    ui.render_process_repository()

    # Set up shorthand variables for session state 
    active_convo = conversations.get_active_convo()

    # Conversation 2: Querying codebase using the given information. Only go here if processed
    if st.session_state.global_messages[active_convo].get("processed"):
        ui.render_conversations() 
        # Else just run as a continuous chatbot query
        conversations.continue_code_convo()


if __name__ == "__main__":
    main()
