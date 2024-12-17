import json
from retrievers import HybridSearch, EnsembleSearch
from langchain_community.document_loaders import DirectoryLoader
from python_ast import PythonASTDocumentLoader
import pandas as pd
from langchain_community.cross_encoders import HuggingFaceCrossEncoder  # BGE
from langchain.retrievers.document_compressors import FlashrankRerank  # Flashrank
from ragatouille import RAGPretrainedModel # Colbert
from langchain.retrievers.document_compressors.cross_encoder_rerank import CrossEncoderReranker

# Naming is messed up: (Class Name) -> (Real Name)
# EnsembleSearch -> Hybrid Retriever
# HybridSearch -> Chained Retriever
def evaluate_retrievers(retrievers, test_cases, ensemble: EnsembleSearch, hybrid:HybridSearch):

    def calculate_mrr(relevant_docs, retrieved_docs):
        """Calculates Mean Reciprocal Rank (MRR) for a single query."""
        for rank, doc in enumerate(retrieved_docs, start=1):
            idx = f"{doc.metadata['relative_path']},{doc.metadata['start_offset']},{doc.metadata['end_offset']}"
            if idx in relevant_docs:
                return 1 / rank
        return 0

    # Metrics to collect
    results = []

    # Test case retriever in JSON
    for retriever in retrievers:
        total_hits = 0
        total_relevant = 0
        total_retrieved = 0
        precision_list = []
        recall_list = []
        f1_list = []
        mrr_list = []

        for case in test_cases:
            query = case["query"]
            relevant_docs = case["relavant"]

            # Initializer Reranker if any
            reranker = None
            if retriever["reranker"] == "None":
                reranker = None
            elif retriever["reranker"] == "flashrank":
                reranker = FlashrankRerank(top_n = retriever["final_k"])
            elif retriever["reranker"] == "bge-reranker-base":
                reranker = CrossEncoderReranker(model=HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-base"), top_n = retriever["final_k"])
            elif retriever["reranker"] == "colbert":
                reranker = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0").as_langchain_document_compressor(k = retriever["final_k"])

            # Retrieve documents
            # Initialize retriever
            if retriever["type"] == "ensemble_retriever":
                retrieved_docs = ensemble.search(query, 
                                                 retriever["weight"], 
                                                 retriever["top_k"], 
                                                 retriever["final_k"], 
                                                 reranker=reranker)
                parameter = {
                    "weight": retriever["weight"], 
                    "top_k": retriever["top_k"], 
                    "final_k": retriever["final_k"], 
                    "reranker": retriever["reranker"]
                }

            elif retriever["type"] == "hybrid_retriever":
                retrieved_docs = hybrid.search(query, 
                                               retriever["bm25_n"], 
                                               retriever["faiss_n"], 
                                               retriever["final_k"], 
                                               reranker=reranker)
                parameter = {
                    "bm25_n": retriever["bm25_n"], 
                    "faiss_n": retriever["faiss_n"],
                    "final_k": retriever["final_k"],
                    "reranker": retriever["reranker"]
                }

            # Calculate hits
            hits = 0
            for doc in retrieved_docs:
                idx = f"{doc.metadata['relative_path']},{doc.metadata['start_offset']},{doc.metadata['end_offset']}"

                if idx in relevant_docs:
                    hits += 1

            total_hits += hits

            # Update totals
            total_relevant += len(relevant_docs)
            total_retrieved += len(retrieved_docs)

            # Precision, Recall, F1
            precision = hits / len(retrieved_docs) if retrieved_docs else 0
            recall = hits / len(relevant_docs) if relevant_docs else 0
            f1 = (2 * precision * recall) / (precision +
                                             recall) if precision + recall > 0 else 0

            precision_list.append(precision)
            recall_list.append(recall)
            f1_list.append(f1)

            # Mean Reciprocal Rank (MRR)
            mrr_list.append(calculate_mrr(relevant_docs, retrieved_docs))

        # Aggregate metrics
        avg_precision = sum(precision_list) / len(test_cases)
        avg_recall = sum(recall_list) / len(test_cases)
        avg_f1 = sum(f1_list) / len(test_cases)
        mrr = sum(mrr_list) / len(test_cases)
        hit_rate = total_hits / total_relevant if total_relevant > 0 else 0

        # Store results
        results.append({
            "Retriever Type": retriever["type"],
            "Parameters": parameter,
            "Hit Rate": hit_rate,
            "Precision": avg_precision,
            "Recall": avg_recall,
            "F1 Score": avg_f1,
            "MRR": mrr
        })

    # Convert results to a pandas DataFrame
    results_df = pd.DataFrame(results)
    return results_df


# Load document
loader = DirectoryLoader("/home/javier/Documents/flask",
                         glob="*.py", loader_cls=PythonASTDocumentLoader, recursive=True)
documents = loader.load()


# Load test variables
with open('RetrieverTester.json', 'r') as file:
    test_vars = json.load(file)
    retrievers = test_vars["retrievers"]
    test_cases = test_vars["payload"]

ensemble = EnsembleSearch(documents)
hybrid = HybridSearch(documents)

result = evaluate_retrievers(retrievers, test_cases, ensemble, hybrid)
result.to_csv("finalResults.csv")
