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
    newContent = f"Block Type: {docs.metadata['block_type']} \n Relative Path: {docs.metadata['relative_path'].replace('/',' ')} \n Block Name: {docs.metadata['block_name']} \n Arguments: {' '.join(docs.metadata['block_args'])} \n Code: {' '.join(re.findall('[a-zA-Z0-9]+', docs.page_content))}"
    docs.page_content = newContent
# db = FAISS.from_documents(documents, embeddings)
# db.save_local(folder_path=os.getcwd()+"/vectorDB")


def customSplitter(listOfDocuments, token_len=2, overlap=1):
    listOfToken = []
    for document in listOfDocuments:
        pagecontent = document.page_content.lower()
        pagecontent = document.page_content.replace("_", " ")
        listToAdd = []
        for x in range(overlap, len(pagecontent), token_len):
            end_index = min(x+token_len, len(pagecontent))
            listToAdd.append(pagecontent[x-overlap:end_index])
        listOfToken.append(listToAdd)
    return listOfToken


def customQuerySplitter(query, token_len=2, overlap=1):
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
                temperature=0.035)

prompt = PromptTemplate(template="""
Context: {context}

You are a Python codebase analyzer. Use the provided repository context to answer questions. Reply the answer and with a code snippet if possible.
If you do now know the answer, just say you do not have enough information.
Cite specific files,function names, and locations in your answers. For example: "(Function: create_new_token, Path: home/User/repo/func.py)".

At the end of your commentary, if you gave a good answer: 
1. Create a list of citations used with (Path, function name)
2. Suggest a further question that can be answered by the paragraphs provided. 


Question: {input} 

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

    inputP = input("What do you want to ask?\n").lower()

    bm25score = bm25.get_scores(customQuerySplitter(query=inputP))
    top_query_bm25_number = min(len(documents), 25)
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
