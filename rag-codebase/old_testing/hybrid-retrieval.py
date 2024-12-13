from langchain_community.document_loaders import DirectoryLoader, TextLoader, PythonLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_ollama import OllamaLLM
# from langchain_community.llms import CTransformers
from langchain_core.prompts import PromptTemplate
# from langchain.chains import RetrievalQA
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.text_splitter import NLTKTextSplitter
import torch


# system_prompt = """
# You are a helpful AI assistant that can answer technical questions about a specific codebase.
# You have access to relevant information from the codebase and can provide insights based on it.
# If none of the code from the codebase answer the question, just say 'I don't know'.
# Always prioritize correctness and clarity in your explanations.
# """

template = """You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
Question: {input} 
Context: {context} 
Answer:"""

loader = DirectoryLoader("../../ast_tokenizer",
                         glob="*.py", loader_cls=PythonLoader, recursive=True)
# interpret information in the documents
documents = loader.load()

for i, v in enumerate(documents):
    print(i, v)
# splitter = RecursiveCharacterTextSplitter(chunk_size=256,
#                                           chunk_overlap=20)
# texts = splitter.split_documents(documents)

# text_splitter = NLTKTextSplitter()
# texts = text_splitter.split_documents(documents)


embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': "cuda"})

# create and save the local database
db = FAISS.from_documents(documents, embeddings)

# template = """Use the following context to answer the user's question. 
# Context: {context}
# Question: {input}
# """

# load the language model
llm = OllamaLLM(model="llama3.1:8b",
                num_predict=-1,
                temperature=0.1)
# llm = CTransformers(model='./llama-2-7b-chat.ggmlv3.q8_0.bin',
#                     model_type='llama',
#                     gpu_layers=50,
#                     config={'max_new_tokens': 1024, 'temperature': 0.05})


# prepare a version of the llm pre-loaded with the local content
bm25_retriever = BM25Retriever.from_documents(documents)
bm25_retriever.k =  5  # Retrieve top 5 results

faiss_retriever = db.as_retriever(search_kwargs={'k': 5})

retriever = EnsembleRetriever(retrievers=[bm25_retriever, faiss_retriever], weights=[0.4, 0.6])
prompt = PromptTemplate(
    template=template,
    input_variables=['context', 'input'])

combine_docs_chain = create_stuff_documents_chain(llm, prompt)
qa_llm = create_retrieval_chain(retriever, combine_docs_chain)

# qa_llm = RetrievalQA.from_chain_type(llm=llm,
#                                      chain_type='stuff',
#                                      retriever=retriever,
#                                      return_source_documents=True,
#                                      chain_type_kwargs={'prompt': prompt})

# ask the AI chat about information in our local files

while True:
    inputP = input("What do you want to ask?\n")
    output = qa_llm.invoke({"input": inputP})
    print(output["answer"])
