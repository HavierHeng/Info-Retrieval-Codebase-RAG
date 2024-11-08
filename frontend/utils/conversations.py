import streamlit as st
from ui import ui
from utils import rag
from utils.llm import (
    DEFAULT_N_PAST_MESSAGES
)


blank_convo = {"repo": None,
               "repo_display_name": "",
               "messages": [],  # Messages are for display
               "active_messages": []  # Active Messages is passed as context to LLM 
               }

def get_active_convo() -> int:
    """
    Returns current index of conversation stored global state
    """
    return st.session_state.active_convo_idx


def update_active_convo(idx: int):
    """
    Updates current index of conversation stored in global state
    """
    st.session_state.update(active_convo_idx=idx)



def add_msgs_to_display(msgs: list[dict]):
    """
    Accepts a list of dictionary of messages to be added 
    Adds messages only for display purposes in the chat into a global state.
    """
    curr_convo = get_active_convo()
    st.session_state.global_messages[curr_convo]["messages"].extend(msgs)


def add_msgs_to_convo(msgs: list[dict]):
    """
    Accepts a list of dictionary of messages to be added 
    Adds messages for both display purposes and as a conversation context for the chat into a global state.
    """
    curr_convo = get_active_convo()
    st.session_state.global_messages[curr_convo]["messages"].extend(msgs)
    st.session_state.global_messages[curr_convo]["active_messages"].extend(msgs)

def setup_repo_convo():
    """
    Conversation to set up repository and repository display name.
    This is the first conversation that gathers user details on what repo they would like to get info on.
    """
    curr_convo = get_active_convo()
    with st.container():  # Use a container to group both inputs
        # Request for both repository URL and display name in the same container
        repo_url, repo_name = ask_for_repo_details()

        if repo_url and repo_name:
            # Store the information in session state
            st.session_state.global_messages[curr_convo]["repo"] = repo_url
            st.session_state.global_messages[curr_convo]["repo_display_name"] = repo_name
            
            # Process the repository (e.g., pulling and indexing)
            process_repository()

def ask_for_repo_details():
    """
    Ask for both the repository URL and display name in a single container.
    The display name is optional and will default to the URL if not provided.
    """
    # Create two input fields side by side
    col1, col2 = st.columns([2, 3])  # Adjust column ratios for layout

    with col1:
        # Repo URL input
        repo_url = st.text_input("Enter Repository URL", "")
    
    with col2:
        # Repo display name input (with default as empty)
        repo_name = st.text_input("Enter Repository Display Name", "")

    if repo_url:
        # Default repo name to repo URL if not provided
        if not repo_name.strip():
            repo_name = repo_url
        return repo_url, repo_name
    else:
        # Return None if no repo URL is provided
        return None, None

def process_repository():
    """
    Process the repository by pulling and indexing it.
    """
    with st.chat_message("assistant"):
        with st.spinner(text="Pulling Repository..."):
            # TODO: Pull repository with gitpython. If fail - break
            print("Imagine pulling a repo here")

        with st.spinner(text="Indexing repository..."):
            # TODO: RAG Preprocessing
            rag.index_repo()
            add_msgs_to_display([{
                "role": "assistant",
                "content": "Finished indexing repository!"
            }])

def start_code_convo():
    """
    Start of conversation to let user query RAG system.
    This is the start of the second conversation that allows users to understand their codebase
    """
    curr_convo = get_active_convo() 

    starting_code_convo = [
        {"role": "system", 
         "content": rag.RAG_SYSTEM_PROMPT.format()},
        {"role": "assistant", 
        "content": f"Hello! I see you are interested in {st.session_state.global_messages[curr_convo]["repo_display_name"]}. How may I help you?"}
    ]

    add_msgs_to_convo(starting_code_convo)


def continue_code_convo():
    """
    Start of conversation to let user query RAG system.
    This is the start of the second conversation that allows users to understand their codebase
    """
    curr_convo = get_active_convo()
    active_messages = st.session_state.global_messages[curr_convo]["active_messages"]

    repo_convo = ui.get_user_chat_input()

    if repo_convo.get("content") is not None:
        add_msgs_to_convo([repo_convo])
        query_result = rag.query_rag(repo_convo["content"])
        # TODO: This is by right the whole conversation + context from RAG
        add_msgs_to_convo([{"role": "assistant",
                           "content": f"{query_result}"}]
                          )

    while len(active_messages) > DEFAULT_N_PAST_MESSAGES + 1:  # limit context window
        active_messages.pop(1)  # preserve system message at index 0


def start_new_convo():
    """
    Starts new conversation and sets current conversation to new index.
    """
    st.session_state.global_messages.append(blank_convo)
    st.session_state.update(active_convo_idx=-1)  # Set to latest conversation


def delete_convo(idx):
    """
    Deletes a conversation from the history - also removes it from the sidebar as a result
    """
    curr_convo = get_active_convo()
    # If deleted conversation is the conversation that user is on
    if idx == curr_convo:
        if curr_convo != 0:
            # Shift user off conversation if not the first conversation
            curr_convo -= 1
        else:
            start_new_convo()
    st.session_state.global_messages.pop(idx)
