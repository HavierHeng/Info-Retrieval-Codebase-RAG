from langchain_community.document_loaders import DirectoryLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from rank_bm25 import BM25Okapi
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

loader = DirectoryLoader("/home/yuesheng/flask",
                         glob="*.py", loader_cls=PythonASTDocumentLoader, recursive=True)
# interpret information in the documents
documents = loader.load()
# augment page data with some meta data
for docs in documents:
    newContent = f"Block Type: {docs.metadata['block_type']} \n Relative Path: {docs.metadata['relative_path'].replace('/',' ')} \n Block Name: {docs.metadata['block_name'].replace('_',' ')} \n Arguments: {' '.join(docs.metadata['block_args'])} \n Code: {' '.join(re.findall('[a-zA-Z0-9]+', docs.page_content))}"
    docs.page_content = newContent
# db = FAISS.from_documents(documents, embeddings)
# db.save_local(folder_path=os.getcwd()+"/vectorDB")


def customSplitter(listOfDocuments, token_len=8, overlap=3):
    listOfToken = []
    for document in listOfDocuments:
        pagecontent = document.page_content.lower()
        listToAdd = []
        for x in range(overlap, len(pagecontent), token_len):
            end_index = min(x+token_len, len(pagecontent))
            listToAdd.append(pagecontent[x-overlap:end_index])
        listOfToken.append(listToAdd)
    return listOfToken


def customQuerySplitter(query, token_len=8, overlap=3):
    listOfToken = []

    for x in range(overlap, len(query), token_len):
        end_index = min(x+token_len, len(query))
        listOfToken.append(query[x-overlap:end_index])
    return listOfToken


# documents = list(db.docstore._dict.values())
tokenized_corpus = customSplitter(documents)
# BM25 initialization

bm25 = BM25Okapi(tokenized_corpus)


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

    bm25score = bm25.get_scores(customQuerySplitter(query=inputP))
    top_query_bm25_number = min(len(documents), 50)
    top_doc_indices = np.argsort(bm25score)[-top_query_bm25_number:]

    top_docs_list = [documents[i] for i in top_doc_indices]
    query_embedings = embeddings.embed_query(inputP)

    tempFaiss = FAISS.from_documents(top_docs_list, embeddings)

    retriever = tempFaiss.as_retriever(search_kwargs={'k': 4})
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
