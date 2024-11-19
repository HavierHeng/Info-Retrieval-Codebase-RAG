import streamlit as st
from ui import ui
from utils import rag
from utils.llm import (
    DEFAULT_N_PAST_MESSAGES
)
from ui import prints
from utils import git_helper
import datetime
import copy

blank_convo = {"repo": None,
               "repo_display_name": "",
               "is_remote": None,  # Is the repo remote or local? This affects the rendering of information
               "repo_owner": "",  # Repo owner, none for local repos
               "repo_commit_sha": "", 
               "repo_branch": "",  # Which branch is indexed in the RAG system
               "repo_path": None, # Where is repo stored - as an OS.PathLike object
               "pull_date": None,  # Datetime for pulling repo
               "processed": False,  # Has repo been cloned and indexed?
               "sidebar_details": False,  # Show sidebar details?
               "messages": [],  # Messages are for display
               "active_messages": [],  # Active Messages is passed as context to LLM 
               "repo_database": None  # RAG database for querying
               }

def get_active_convo() -> int:
    """
    Returns current index of conversation stored global state
    """
    return st.session_state.active_convo_idx if st.session_state.active_convo_idx != -1 else len(st.session_state.global_messages) - 1


def update_active_convo(idx: int):
    """
    Updates current index of conversation stored in global state
    """
    st.session_state.update(active_convo_idx=idx)

def add_msgs_to_context(convo:int, msgs: list[dict]):
    """
    Accepts a list of dictionary of messages to be added 
    Adds messages only for context purposes in the chat into a global state.
    """
    st.session_state.global_messages[convo]["active_messages"].extend(msgs)

def add_msgs_to_display(convo: int, msgs: list[dict]):
    """
    Accepts a list of dictionary of messages to be added 
    Adds messages only for display purposes in the chat into a global state.
    """
    st.session_state.global_messages[convo]["messages"].extend(msgs)

def add_msgs_to_convo(convo:int, msgs: list[dict]):
    """
    Accepts a list of dictionary of messages to be added 
    Adds messages for both display purposes and as a conversation context for the chat into a global state.
    """
    st.session_state.global_messages[convo]["messages"].extend(msgs)
    st.session_state.global_messages[convo]["active_messages"].extend(msgs)

def start_new_convo():
    """
    Starts new conversation and sets current conversation to new index.
    This is the first conversation that gathers user details on what repo they would like to get info on.
    """
    st.session_state.global_messages.append(copy.deepcopy(blank_convo))  # Python passes by reference for mutables like dicts
    st.session_state.update(active_convo_idx=-1)  # Set to latest conversation
    setup_repo_convo()

def setup_repo_convo():
    """
    Conversation to set up repository and repository display name.
    If repository and repository display name is set, then check if repo has been cloned and indexed
    This is the first conversation that gathers user details on what repo they would like to get info on.
    """
    curr_convo = get_active_convo()
    if not(st.session_state.global_messages[curr_convo].get("repo") and st.session_state.global_messages[curr_convo].get("repo_display_name")):
        # Setup flag to render new conversation - implemented in UI
        st.session_state.animation["new_convo"] = True
    else:
        # If already set repo and display name, but not processed
        if not st.session_state.global_messages[curr_convo].get("processed"):
            # Setup flag to render processing repo- implemented in UI
            st.session_state.animation["process_repo"] = True
        

def process_local_repository():
    """
    Process the local repository by indexing it.
    """
    indexed = False
    with st.chat_message("assistant"):
        repo_path = st.session_state.global_messages[get_active_convo()].get("repo")
        repo_name = st.session_state.global_messages[get_active_convo()].get("repo_display_name")
        rag_db = st.session_state.global_messages[get_active_convo()].get("repo_database")
        st.session_state.global_messages[get_active_convo()]["repo_path"] = repo_path

        with st.spinner(text="Indexing local repository..."):
            if rag_db is None:
                st.session_state.global_messages[get_active_convo()]["repo_database"] = rag.RAG_Database(repo_path)
            indexed = rag_db.index_repo()
            st.toast(f"Repository {repo_name} at {repo_path} indexed.")

        if indexed: 
            st.write("Repository has been processed!")
            sha_commit, repo_branch = git_helper.get_latest_local_commit_sha(repo_path)
            st.session_state.global_messages[get_active_convo()]["repo_owner"] = git_helper.get_repo_owner_name_from_url(repo_path)[0]
            st.session_state.global_messages[get_active_convo()]["repo_commit_sha"] = sha_commit
            st.session_state.global_messages[get_active_convo()]["repo_branch"] = repo_branch
            st.session_state.global_messages[get_active_convo()]["pull_date"] = datetime.datetime.now()
            st.toast(f"Repository {repo_name} (Commit SHA: {sha_commit}) has finished cloning and indexing.")
    return indexed

def process_remote_repository():
    """
    Process the remote repository by pulling and indexing it.
    """
    cloned = False
    indexed = False
    with st.chat_message("assistant"):
        repo_url = st.session_state.global_messages[get_active_convo()].get("repo")
        repo_name = st.session_state.global_messages[get_active_convo()].get("repo_display_name")
        rag_db = st.session_state.global_messages[get_active_convo()].get("repo_database")
        with st.spinner(text="Cloning Repository..."):
            # ui.display_clone_progress()
            cloned = git_helper.clone_repo(repo_url)
            if cloned:
                st.toast(f"Repository {repo_name} at {repo_url} cloned.")
                st.session_state.global_messages[get_active_convo()]["repo_path"] = cloned

        with st.spinner(text="Indexing repository..."):
            repo_path = st.session_state.global_messages[get_active_convo()].get("repo_path")
            if rag_db is None:
                st.session_state.global_messages[get_active_convo()]["repo_database"] = rag.RAG_Database(repo_path)
            indexed = rag_db.index_repo()
            st.toast(f"Repository {repo_name} indexed.")

        if cloned and indexed: 
            st.write("Repository has been processed!")
            sha_commit, repo_branch = git_helper.get_latest_remote_commit_sha(repo_url)
            st.session_state.global_messages[get_active_convo()]["repo_owner"] = git_helper.get_repo_owner_name_from_url(repo_url)[0]
            st.session_state.global_messages[get_active_convo()]["repo_commit_sha"] = sha_commit
            st.session_state.global_messages[get_active_convo()]["repo_branch"] = repo_branch
            st.session_state.global_messages[get_active_convo()]["pull_date"] = datetime.datetime.now()
            st.toast(f"Repository {repo_name} (Commit SHA: {sha_commit}) has finished cloning and indexing.")
    return cloned and indexed

def start_code_convo(curr_convo):
    """
    Start of conversation to let user query RAG system.
    This is the start of the second conversation that allows users to understand their codebase
    """
    assistant_init_msg = {"role": "assistant", 
                          "content": f"Hello! I see you are interested in {st.session_state.global_messages[curr_convo]['repo_display_name']}. How may I help you?"}
    starting_code_convo = [
        {"role": "system", 
         "content": rag.RAG_SYSTEM_PROMPT.format()},
        assistant_init_msg
    ]
    # Only display assistant, the system prompt is invisible
    add_msgs_to_context(curr_convo, starting_code_convo)
    add_msgs_to_display(curr_convo, [assistant_init_msg])


def continue_code_convo():
    """
    Start of conversation to let user query RAG system.
    This is the start of the second conversation that allows users to understand their codebase
    """
    curr_convo = get_active_convo()
    active_messages = st.session_state.global_messages[curr_convo]["active_messages"]
    rag_db = st.session_state.global_messages[curr_convo]["repo_database"]

    repo_convo = ui.get_user_chat_input()

    if repo_convo is not None:
        add_msgs_to_convo(curr_convo, [repo_convo])
        st.chat_message("user").write_stream(prints.fake_print_stream(repo_convo["content"]))
        with st.spinner("Thinking..."):
            query_result = rag_db.query_rag(repo_convo["content"])
            st.chat_message("assistant").write_stream(prints.fake_print_stream(query_result))  # Fix the rendering bug since it doesn't refresh right away
            add_msgs_to_convo(curr_convo, [{"role": "assistant", 
                                            "content": f"{query_result}"}])

    while len(active_messages) > DEFAULT_N_PAST_MESSAGES + 1:  # limit context window
        active_messages.pop(1)  # preserve system message at index 0


def delete_convo(idx, is_remote):
    """
    Deletes a conversation from the history - also removes it from the sidebar as a result.
    It also deletes any cloned repos at the path if it does exist if its a remote repo.
    Does not delete repos is its a local repo!
    """
    curr_convo = get_active_convo()
    # If deleted conversation is the conversation that user is on
    if idx == curr_convo:
        if curr_convo != 0:
            # Shift user off conversation before popping if same idx
            st.session_state.active_convo_idx -= 1
        else:
            # Create new convo if same idx
            start_new_convo()
    repo_path = st.session_state.global_messages[curr_convo].get("repo_path")
    if repo_path:
        if is_remote:  # If remote, delete repo. 
            git_helper.delete_downloaded_repo(repo_path)
        else:  # Else if local, do not nuke the repo
            print(f"Local repo, will not delete {repo_path}.")
    st.session_state.global_messages.pop(idx)
