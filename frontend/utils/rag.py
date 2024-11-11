import time
from utils import conversations
import glob
import streamlit as st 

# TODO: Placeholders
RAG_SYSTEM_PROMPT = "You are a programmer working on this codebase. You are to help the user understand the code base as much as possible"
RAG_CONTEXT_PROMPT = "For the user query, here are some relevant information about the code that will help you."

def index_repo():
    """
    TODO: Once RAG has been experimented with
    """
    time.sleep(2)
    return True

def query_rag(query):
    """
    TODO: Once RAG has been experimented with
    """
    placeholder = glob.glob(query, root_dir=st.session_state.global_messages[conversations.get_active_convo()].get("repo_path"))  # For now is just all files that matches glob path
    if len(placeholder) == 0:
        placeholder = f"Nothing found - Echo: {query}"
    return f"PLACEHOLDER MESSAGE: {placeholder}"
