import streamlit as st
import time
from utils import conversations
import glob
from langchain_community.document_loaders import DirectoryLoader, PythonLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath('')), '../ast_tokenizer/languages')))
# from languages.python_ast import PythonASTDocumentLoader
# from languages.javascript_ast import JavascriptASTDocumentLoader


DEFAULT_EMBEDDING = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2", model_kwargs={'device': "cuda"})
RAG_TEMPLATE = """Use the following context to answer the user's question. 
    Context: {context}
    Question: {input}
    """
OLLAMA_LLM_MODEL = OllamaLLM(model="llama3.1:8b", num_predict=-1, temperature=0.1)
RAG_SYSTEM_PROMPT = "You are a programmer working on this codebase. You are to help the user understand the code base as much as possible"
RAG_CONTEXT_PROMPT = "For the user query, here are some relevant information about the code that will help you."

class RAG_Database:
    def __init__(self, repo_path, embeddings = DEFAULT_EMBEDDING):
        self.repo_path = repo_path
        loader = DirectoryLoader(repo_path, glob="*.py", loader_cls=PythonLoader, recursive=True)  # TODO: Hardcoded to Python only for now
        self.documents = loader.load()
        self.embeddings = embeddings
        self.llm = OLLAMA_LLM_MODEL
        
    def index_repo(self) -> bool:
        """
        Indexes repo - will return False if not successful
        """
        if self.documents:
            self.db = FAISS.from_documents(self.documents, self.embeddings)
            retriever = self.db.as_retriever(search_kwargs={'k': 5})
            prompt = PromptTemplate(
                template=RAG_TEMPLATE,
                input_variables=['context', 'input'])
            combine_docs_chain = create_stuff_documents_chain(self.llm, prompt)
            self.qa_llm = create_retrieval_chain(retriever, combine_docs_chain)
            return True
        return False

    def query_rag(self, query):
        output = self.qa_llm.invoke({"input": query})
        return output["answer"]


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
