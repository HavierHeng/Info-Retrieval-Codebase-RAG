from langchain_community.document_loaders import DirectoryLoader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath('')), '../ast_tokenizer/languages')))
from ...ast_tokenizer.languages.python_ast import PythonASTDocumentLoader
from ...ast_tokenizer.languages.javascript_ast import JavascriptASTDocumentLoader



class RAG_Database:
    DEFAULT_EMBEDDING = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2", model_kwargs={'device': "cuda"})
    RAG_TEMPLATE = """Use the following context to answer the user's question. 
        Context: {context}
        Question: {input}
        """
    OLLAMA_LLM_MODEL = OllamaLLM(model="llama3.1:8b", num_predict=-1, temperature=0.1)
    RAG_SYSTEM_PROMPT = "You are a programmer working on this codebase. You are to help the user understand the code base as much as possible"
    RAG_CONTEXT_PROMPT = "For the user query, here are some relevant information about the code that will help you."
    def __init__(self, repo_path, embeddings = DEFAULT_EMBEDDING):
        self.repo_path = repo_path
        py_loader = DirectoryLoader(repo_path, glob="*.py", loader_cls=PythonASTDocumentLoader, recursive=True)
        js_loader = DirectoryLoader(repo_path, glob="*.js", loader_cls=JavascriptASTDocumentLoader, recursive=True)
        self.documents = py_loader.load() + js_loader.load()
        self.embeddings = embeddings
        
    def full_index_repo(self):
        self.db = FAISS.from_documents(self.documents, self.embeddings)
        retriever = self.db.as_retriever(search_kwargs={'k': 5})
        prompt = PromptTemplate(
            template=RAG_Database.RAG_TEMPLATE,
            input_variables=['context', 'input'])
        combine_docs_chain = create_stuff_documents_chain(RAG_Database.OLLAMA_LLM_MODEL, prompt)
        self.qa_llm = create_retrieval_chain(retriever, combine_docs_chain)

    def full_query_rag(self, query):
        output = self.qa_llm.invoke({"input": query})
        return output["answer"]


# import streamlit as st
# import time
# from utils import conversations
# import glob
# class RAG_Database:
#     def __init__(self, repo_path):
#         self.repo_path = repo_path
# 
#     def index_repo(self):
#         time.sleep(2)
#         return True
# 
#     def query_rag(self, query):
#         placeholder = glob.glob(query, self.repo_path)  # For now is just all files that matches glob path
#         if len(placeholder) == 0:
#             placeholder = f"Nothing found - Echo: {query}"
#         return f"PLACEHOLDER MESSAGE: {placeholder}"
