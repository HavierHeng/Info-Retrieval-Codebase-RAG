import numpy as np
from rank_bm25 import BM25Okapi
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain.retrievers.document_compressors.cross_encoder_rerank import CrossEncoderReranker
from typing import Optional

import re
from copy import deepcopy

class HybridSearch:
    def __init__(self, documents, token_len=2, overlap=1):
        self.token_len = token_len
        self.overlap = overlap
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/multi-qa-mpnet-base-cos-v1",
            model_kwargs={'device': "cuda"})
        # BM25 initialization
        documents = deepcopy(documents)
        for docs in documents:
            newContent = f"Block Type: {docs.metadata['block_type']} \n\
                Relative Path: {docs.metadata['relative_path']},{docs.metadata['start_offset']},{docs.metadata['end_offset']} \n \
                Block Name: {docs.metadata['block_name']} \n\
                Arguments: {' '.join(docs.metadata['block_args'])} \n\
                Code: {' '.join(re.findall('[a-zA-Z0-9]+', docs.page_content))}"
            docs.page_content = newContent
        self.documents = documents
        tokenized_corpus = self.customSplitter(self.documents)
        self.bm25 = BM25Okapi(tokenized_corpus)

        # Sentence transformer for embeddings

    def search(self, query, bm25_n=25, faiss_n=10, final_k=5, reranker:Optional[CrossEncoderReranker] = None):
        # BM25 search
        bm25score = self.bm25.get_scores(self.customQuerySplitter(query))
        top_query_bm25_number = min(len(self.documents), bm25_n)
        top_doc_indices = np.argsort(bm25score)[-top_query_bm25_number:]
        top_docs_list = [self.documents[i] for i in top_doc_indices]

        tempFaiss = FAISS.from_documents(top_docs_list, self.embeddings)

        # FAISS search on the top documents
        retriever = tempFaiss.as_retriever(search_kwargs={'k': faiss_n})

        ranked_docs = retriever.invoke(query)

        if reranker:
            ranked_docs = reranker.compress_documents(ranked_docs, query)

        ranked_docs = ranked_docs[:final_k]

        return ranked_docs

    def customSplitter(self, listOfDocuments):
        listOfToken = []
        for document in listOfDocuments:
            pagecontent = document.page_content.lower()
            pagecontent = document.page_content.replace("_", " ")
            listToAdd = []
            for x in range(self.overlap, len(pagecontent), self.token_len-self.overlap):
                end_index = min(x+self.token_len, len(pagecontent))
                listToAdd.append(pagecontent[x-self.overlap:end_index])
            listOfToken.append(listToAdd)
        return listOfToken

    def customQuerySplitter(self, query):
        listOfToken = []

        for x in range(self.overlap, len(query), self.token_len-self.overlap):
            end_index = min(x+self.token_len, len(query))
            listOfToken.append(query[x-self.overlap:end_index])
        return listOfToken


class EnsembleSearch:
    def __init__(self, documents, token_len=2, overlap=1):
        self.token_len = token_len
        self.overlap = overlap
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/multi-qa-mpnet-base-cos-v1",
            model_kwargs={'device': "cuda"})

        # all-MiniLM-L6-v2
        # multi-qa-mpnet-base-cos-v1
        # BM25 initialization
        documents = deepcopy(documents)
        for docs in documents:
            newContent = f"Block Type: {docs.metadata['block_type']} \n\
                Relative Path: {docs.metadata['relative_path']},{docs.metadata['start_offset']},{docs.metadata['end_offset']} \n \
                Block Name: {docs.metadata['block_name']} \n\
                Arguments: {' '.join(docs.metadata['block_args'])} \n\
                Code: {' '.join(re.findall('[a-zA-Z0-9]+', docs.page_content))}"
            docs.page_content = newContent
        self.documents = documents
        self.bm25_retriever = BM25Retriever.from_documents(
            documents, preprocess_func=self.customSplitter)

        self.db = FAISS.from_documents(documents, self.embeddings)

    def search(self, query, weight, top_n=10, final_k=5, reranker:Optional[CrossEncoderReranker] = None):
        # Hybrid extracts twice the final number of retrieved docs, reranks and takes the top few.

        self.bm25_retriever.k = 2*top_n
        faiss_retriever = self.db.as_retriever(search_kwargs={'k': 2*top_n})
        retriever = EnsembleRetriever(
            retrievers=[self.bm25_retriever, faiss_retriever], weights=weight)
        ranked_docs = retriever.invoke(query)

        if reranker:
            ranked_docs = reranker.compress_documents(ranked_docs, query)
        ranked_docs = ranked_docs[:final_k]

        return ranked_docs 

    def customSplitter(self, strIn):
        listOfToken = []

        for x in range(self.overlap, len(strIn), self.token_len):
            end_index = min(x+self.token_len, len(strIn))
            listOfToken.append(strIn[x-self.overlap:end_index])
        return listOfToken
