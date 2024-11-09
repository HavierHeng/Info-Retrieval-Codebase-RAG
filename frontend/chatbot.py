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
            "new_convo": False
        }

    # Active conversation index - just keeps track of which conversation user is currently sending data to/rendering
    if "active_convo_idx" not in st.session_state:
        conversations.start_new_convo()
    else:
        # Uninitialized session
        if st.session_state.global_messages[conversations.get_active_convo()].get("repo") is None:
            conversations.setup_repo_convo()


def main():
    """
    Main loop for streamlit application
    """
    st.title("Codebase RAG Chatbot") 
    init_session_state()

    ui.render_sidebar()
    ui.render_conversations()  
    ui.render_new_conversation()
    # Set up shorthand variables for session state 
    active_convo = conversations.get_active_convo()
    active_messages = st.session_state.global_messages[active_convo]["active_messages"]

    # Conversation 1: Setting up codebase by pulling repo and indexing source code
    #    conversations.setup_repo_convo()
        # st.rerun()  # Force reload to Conversation 2 without user intervention. Forces rerendering of button 

    # Conversation 2: Querying codebase using the given information 
    if st.session_state.global_messages[active_convo]["repo"] is not None:
        # Chat transition only on first proper query
        if len(active_messages) == 0:
            conversations.start_code_convo()  # Regenerate messages
            st.rerun()
        # Else just run as a continuous chatbot query
        conversations.continue_code_convo()


if __name__ == "__main__":
    main()
