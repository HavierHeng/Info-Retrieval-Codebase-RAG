from langchain_community.document_loaders import DirectoryLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_ollama import ChatOllama
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langgraph.graph import START, StateGraph
from python_ast import PythonASTDocumentLoader
from rag_citations import *
from typing import TypedDict
import os
import re
import copy
import pathlib

folderPath = os.getcwd()+"/vectorDB"

def augment_docs_with_metadata(docs: List[Document]):
    """
    Reformats Docs, combining metadata into its page content 
    """
    for doc in docs:
        newContent = f""" Block Type: {doc.metadata['block_type']}
        Relative Path: {doc.metadata['relative_path'].replace('/',' ')}
        Block Name: {doc.metadata['block_name'].replace('_',' ')}
        Arguments: {' '.join(doc.metadata['block_args'])} 
        Code: {' '.join(re.findall('[a-zA-Z0-9]+', doc.page_content))}
        """
        doc.page_content = newContent

def reformat_docs_with_id(docs: List[Document]) -> str:
    """
    Adds a Source ID field to each Document. Does not modify the original, makes a copy. Returns a concat str of all the documents provided.
    """
    formatted_docs = [f"Source ID: {i}{doc.page_content}" for i, doc in enumerate(docs)]
    return "\n\n".join(formatted_docs) 

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/multi-qa-mpnet-base-cos-v1",
    model_kwargs={'device': "cuda"})

repo_path = str(pathlib.PosixPath("~/Documents/flask").expanduser())

loader = DirectoryLoader(repo_path,
                         glob="*.py", 
                         loader_cls=PythonASTDocumentLoader, 
                         recursive=True)

documents = loader.load()
print(f"Loaded {len(documents)} documents.")
augment_docs_with_metadata(documents)

# L2 Dense Embedding Index
db = FAISS.from_documents(documents, embeddings)
faiss_retriever = db.as_retriever(search_kwargs={'k': 2})

# BM25 Sparse Index
bm25_retriever = BM25Retriever.from_documents(documents)
bm25_retriever.k = 2  # Retrieve top 5 results

# Ensemble Retrievers into Hybrid Retriever
retriever = EnsembleRetriever(retrievers=[bm25_retriever, faiss_retriever], weights=[0.6, 0.4])

# Load LLM - ChatOllama is newer than OllamaLLM and supports new features like function calling
llm = ChatOllama(model="llama3.1:8b",
                num_predict=-1,
                temperature=0)

# llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")

# Prompt with inline citations
prompt = PromptTemplate(template="""
Context: 
{context}

You are a Python codebase analyzer. Use the provided repository context to answer questions. Reply the answer with code snippets if possible. If you are unable to answer, then say so.

Question: {input} 

Answer:""", input_variables=['input', 'context'])

# Defines state storage for RAG
# Using LangGraph allows clean injection of ref no. into retrieved documents
class State(TypedDict):
    question: str
    context: List[Document]
    answer: str

# Define Retrieval Step
def retrieve(state: State):
    retrieved_docs = retriever.invoke(state["question"])
    return {"context": retrieved_docs}

# Define Generator Step
def generate(state: State):
    formatted_docs = reformat_docs_with_id(state["context"])
    gen_message = prompt.invoke({"input": state["question"], "context": formatted_docs})
    structured_llm = llm.with_structured_output(CitedAnswer)
    # If it has an error here, update ollama package with pip
    response = structured_llm.invoke(gen_message)
    return {"answer": response}

graph_builder = StateGraph(State).add_sequence([retrieve, generate])
graph_builder.add_edge(START, "retrieve")
graph = graph_builder.compile()

questions = ["How do I deserialize json data?",
    "How do I start up a flask app server?",
    "How do I configure routes?",
    "How do I create a custom error handler?",
    "Does flask handle password hashing?",
    "Does flask have ORM features?",
    "How do I set up logging in flask?",
    "Are there ways to implement test cases for my flask application?",
    "Can you render frontend with flask?",
    "How do I implement middleware?"]

# questions = [ "How do I implement middleware?"]

for question in questions:
    # qa_chain = create_stuff_documents_chain(llm, prompt)
    # rag_chain = create_retrieval_chain(retriever, qa_chain)
    context = []

    print("Question:", question)
    # for chunk in rag_chain.stream({"input": question}):
    result = graph.invoke({"question": question})
    context = result["context"] 
    # print(result["answer"])
    print("Answer:")
    for inline_answer in result["answer"].answers:
        print(f"{inline_answer.answer} {inline_answer.source_id}")

    print("Citations:")
    for citation in result["answer"].citations:
        print(f"{citation.source_id}) {citation.quote}")

    print()


    # for chunk in graph.stream({"question": question}):
    #     if 'context' in chunk.keys():
    #         print("Retrieved Docs from")
    #         for d in chunk['context']:
    #             context.append(d.page_content)
    #             print(
    #                 f"Folder:{d.metadata['relative_path']} Block Type{d.metadata['block_type']} Function name: {d.metadata['block_name']}")
    #     elif 'answer' in chunk.keys():
    #         print(chunk['answer'], end="", flush=True)
    # print()
    # print("Context:", context)
    # print()
