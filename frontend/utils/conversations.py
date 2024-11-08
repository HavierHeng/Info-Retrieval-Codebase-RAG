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
    st.session_state[curr_convo]["active_messages"].extend(msgs)


def setup_repo_convo():
    """
    Conversation to set up repository and repository display name
    This is the first conversation that gathers user details on what repo they would like to get info on.
    """
    curr_convo = get_active_convo()
    repo_query = [ 
                    {"role": "assistant",
                    "content": "Hello there! Please provide a repository link that you are interested to get information about!"}
                ]

    add_msgs_to_display(repo_query)

    repo_url_reply = ui.get_user_chat_input()

    if repo_url_reply is not None:
        st.session_state[curr_convo]["repo"] = repo_url_reply["content"]
        add_msgs_to_display([repo_url_reply])

        name_query = [ 
                    {"role": "assistant",
                     "content": f"Would you like to rename this repository? Current Name: {repo_url_reply["content"]}"}
                ]

        add_msgs_to_display(name_query)

        repo_name_reply = ui.get_user_chat_input()

        if repo_name_reply is not None:
            # If user does not want to input anything
            if len(repo_name_reply["content"].strip()) == 0:
                repo_name_reply["content"] = repo_url_reply["content"]
            st.session_state[curr_convo]["repo_display_name"] = repo_name_reply["content"]
            add_msgs_to_display([repo_name_reply])
    
    with st.chat_message("assistant"):
        with st.spinner(text="Pulling Repository..."):
            # TODO: Pull repository with gitpython. If fail - break
            print("Imagine pulling a repo here")


        with st.spinner(text="Indexing repository..."):
            # TODO: RAG Preprocessing
            rag.index_repo()

    add_msgs_to_display([{
                        "role": "assistant",
                        "content": f"Finished indexing repository."
                        }])


def start_repo_convo():
    """
    Start of conversation to let user query RAG system.
    This is the start of the second conversation that allows users to understand their codebase
    """
    curr_convo = get_active_convo() 

    repo_convo = [
        {"role": "system", 
         "content": rag.RAG_SYSTEM_PROMPT.format()},
        {"role": "assistant", 
        "content": f"Hello! I see you are interested in {st.session_state[curr_convo]["repo_display_name"]}. How may I help you?"}
    ]

    add_msgs_to_convo(repo_convo)


def continue_repo_convo():
    """
    Start of conversation to let user query RAG system.
    This is the start of the second conversation that allows users to understand their codebase
    """
    curr_convo = get_active_convo()
    active_messages = st.session_state.global_messages[curr_convo]["active_messages"]

    repo_convo = ui.get_user_chat_input()

    if repo_convo is not None:
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
    setup_repo_convo()


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
