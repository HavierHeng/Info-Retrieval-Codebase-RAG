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

# if os.path.isdir(folderPath):
#     db = FAISS.load_local(
#         folderPath, embeddings, allow_dangerous_deserialization=True)
# else:

loader = DirectoryLoader("../../ast_tokenizer",
                         glob="*.py", loader_cls=PythonASTDocumentLoader, recursive=True)
# interpret information in the documents
documents = loader.load()

# interpreting the output from the docs
# for doc in documents:
#     print(doc.page_content)
#     print(doc.metadata)
#     print("\n")
#     break

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

retriever = EnsembleRetriever(retrievers=[bm25_retriever, faiss_retriever], weights=[0.7, 0.3])

# load the language model
llm = OllamaLLM(model="llama3.1:8b",
                num_predict=-1,
                temperature=0.05)

prompt = PromptTemplate(template="""
You are a master python programmer. Use the following pieces of retrieved context to answer the question. 
If you don't know the answer, just say that you don't know. The context will simplified python code.

Question: {input} 

Context: {context} 

Answer:""",
input_variables=['input', 'context'])


# qa_llm = RetrievalQA.from_chain_type(llm=llm,
#                                      chain_type='stuff',
#                                      retriever=retriever,
#                                      return_source_documents=True,
#                                      chain_type_kwargs={'prompt': prompt})

# ask the AI chat about information in our local files


# rag_chain = (
#     {"context": retriever | format_docs, "question": RunnablePassthrough()}
#     | prompt
#     | llm
#     | StrOutputParser()
# )


while True:

    inputP = input("What do you want to ask?\n")
    qa_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, qa_chain)

    for chunk in rag_chain.stream({"input": inputP}):
        if 'context' in chunk.keys():
            print("Retrieved Docs from")
            for d in chunk['context']:
                print(
                    f"Folder:{d.metadata['relative_path']} Block Type{d.metadata['block_type']} Function name: {d.metadata['block_name']}")
        elif 'answer' in chunk.keys():
            print(chunk['answer'], end="", flush=True)
    print()
