from langchain_community.document_loaders import DirectoryLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
# from rank_bm25 import BM25Okapi
import numpy as np
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
import os
from python_ast import PythonASTDocumentLoader
import time
import re

folderPath = os.getcwd()+"/vectorDB"


embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/multi-qa-mpnet-base-cos-v1",
    model_kwargs={'device': "cuda"})

loader = DirectoryLoader("../../../flask",
                         glob="*.py", loader_cls=PythonASTDocumentLoader, recursive=True)
# interpret information in the documents

documents = loader.load()
# augment page data with some meta data
for docs in documents:
    newContent = f"""Block Type: {docs.metadata['block_type']}
    Relative Path: {docs.metadata['relative_path'].replace('/',' ')}
    Block Name: {docs.metadata['block_name'].replace('_',' ')}
    Arguments: {' '.join(docs.metadata['block_args'])} 
    Code: {' '.join(re.findall('[a-zA-Z0-9]+', docs.page_content))}"""
    docs.page_content = newContent
# db = FAISS.from_documents(documents, embeddings)
# db.save_local(folder_path=os.getcwd()+"/vectorDB")

db = FAISS.from_documents(documents, embeddings)

bm25_retriever = BM25Retriever.from_documents(documents)
bm25_retriever.k = 2  # Retrieve top 5 results

faiss_retriever = db.as_retriever(search_kwargs={'k': 2})

retriever = EnsembleRetriever(retrievers=[bm25_retriever, faiss_retriever], weights=[0.6, 0.4])

# load the language model
llm = OllamaLLM(model="llama3.1:8b",
                num_predict=-1,
                temperature=0)

prompt = PromptTemplate(template="""
Context: {context}

You are a Python codebase analyzer. Use the provided repository context to answer questions. Reply the answer and with a code snippet if possible.
- If you do now know the answer, just say you do not have enough information.
- Use inline numerical citations [1], [2], etc. immediately after referencing any content from the provided documents
- If there are multiple references to the same document, use the same citation number
- If a specific line or section of code is directly used, place the citation right after that specific reference

At the end of your commentary, if you gave a good answer: 
1. Create a list of citations used with (Path, function name)
2. Cite specific files,function names, and locations in your answers. For example: "1. (Function: create_new_token, Path: home/User/repo/func.py)".
3. Use "/" as standard path separator.                
Question: {input} 

Answer:""", input_variables=['input', 'context'])

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

# while True:
for question in questions:
    # inputP = input("What do you want to ask?\n")

    qa_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, qa_chain)
    context = []

    print("Question:", question)
    for chunk in rag_chain.stream({"input": question}):
        if 'context' in chunk.keys():
            print("Retrieved Docs from")
            for d in chunk['context']:
                context.append(d.page_content)
                print(
                    f"Folder:{d.metadata['relative_path']} Block Type{d.metadata['block_type']} Function name: {d.metadata['block_name']}")
        elif 'answer' in chunk.keys():
            print(chunk['answer'], end="", flush=True)
    print("\n")
    print("context:", context)
    print()
