import streamlit as st
from ui import ui
from ui import prints
from utils import conversations


# Initial page setup
st.set_page_config(page_title="Codebase Query Helper", page_icon="🤖💬", layout="centered")
st.title("Codebase RAG Chatbot") 

def init_session_state():
    """
    Sets up global session state if not already set up.

    Session state is in this format:
    
    session_state = {
        "global_messages": [
                {"repo": None,
               "repo_display_name": "",
               "messages": [],  
               "active_messages": []
               },
                {"repo": None,
               "repo_display_name": "",
               "messages": [],  
               "active_messages": []
               },
               ...
        ],
        "active_convo_idx": int
    }
    """
    if "global_messages" not in st.session_state:
        st.session_state.global_messages = []

    if "active_convo_idx" not in st.session_state:
        conversations.start_new_convo()


def main():
    """
    Main loop for streamlit application
    """
    init_session_state()
    ui.render_sidebar()
    ui.render_conversations()

    # Set up shorthand variables for session state 
    active_convo = conversations.get_active_convo()
    active_messages = st.session_state.global_messages[active_convo]["active_messages"]

    # Conversation 1: Setting up codebase by pulling repo and indexing source code
    if st.session_state.global_messages[active_convo]["repo"] is None:
        conversations.setup_repo_convo()

        st.rerun()  # Force reload to Conversation 2 without user intervention. Forces rerendering of button 

    # Conversation 2: Querying codebase using the given information 
    else:  
        if len(active_messages) == 0:
            conversations.start_repo_convo()  # Regenerate messages
            st.rerun()

        conversations.continue_repo_convo()



if __name__ == "__main__":
    main()
