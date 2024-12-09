from retrievers import HybridSearch, EnsembleSearch
from langchain_community.document_loaders import DirectoryLoader
from python_ast import PythonASTDocumentLoader
import json
import numpy as np
import os
dir_path = os.path.dirname(os.path.realpath(__file__))


def tabSpacer(input, cell=1, charspace=12):
    input = str(input)
    if len(input) > cell*charspace:
        return input[:charspace]
    else:
        return str(" "*((charspace*cell)-len(input))+input)


# Load document
loader = DirectoryLoader("/home/yuesheng/flask",
                         glob="*.py", loader_cls=PythonASTDocumentLoader, recursive=True)
documents = loader.load()

# Load test variables
with open('testFile.json', 'r') as file:
    test_vars = json.load(file)

results = []

search1 = HybridSearch(documents)
curr_path = dir_path+"/hybrid"
f_avg = open(
    f"{curr_path}/average_fscore.txt", "w")
cols = [tabSpacer(x) for x in test_vars["hybrid_retriever"]["faiss_n"]]
f_avg.write(tabSpacer("bm\\faiss")+"|"+"|".join(cols)+'\n')
for bm25_n in test_vars["hybrid_retriever"]["bm25_n"]:
    f_avg.write(f'{tabSpacer(bm25_n)}')
    for faiss_n in test_vars["hybrid_retriever"]["faiss_n"]:
        print(f"BM25: Top {bm25_n}, FAISS: Top {faiss_n}")

        f_indiv = open(
            f"{curr_path}/individual_results/bm{bm25_n}_faiss{faiss_n}.txt", "w")
        f_indiv.write(
            f"{tabSpacer('doc_idx')}|{tabSpacer('recall')}|{tabSpacer('precision')}|{tabSpacer('fscore')}\n")
        list_fscore = []
        for i, x in enumerate(test_vars["payload"]):
            retrieved_docs = search1.search(x["query"], bm25_n, faiss_n)
            total_retrieved, relevant_retrieved = 0, 0
            total_relevant = len(x["relavant"])
            for doc in retrieved_docs:
                idx = f"{doc.metadata['relative_path']},{doc.metadata['start_offset']},{doc.metadata['end_offset']}"
                if idx in x["relavant"]:
                    relevant_retrieved += 1
                total_retrieved += 1
            if relevant_retrieved == 0:
                recall = 0
                precision = 0
                fscore = 0
            else:
                recall = relevant_retrieved/total_relevant
                precision = relevant_retrieved/total_retrieved
                fscore = (2*precision*recall)/(precision+recall)
            list_fscore.append(fscore)
            f_indiv.write(
                f"{tabSpacer(i)}|{tabSpacer(recall)}|{tabSpacer(precision)}|{tabSpacer(fscore)}\n")
        f_indiv.close()
        avg_fscore = np.average(list_fscore)
        f_avg.write("|"+tabSpacer(avg_fscore))
    f_avg.write("\n")
f_avg.close()
search2 = EnsembleSearch(documents)
curr_path = dir_path+"/ensemble"
f_avg = open(
    f"{curr_path}/average_fscore.txt", "w")
cols = [tabSpacer(x) for x in test_vars["ensemble_retriever"]["top_k"]]
f_avg.write(tabSpacer("weight\\k")+"|"+"|".join(cols)+'\n')
for weight in test_vars["ensemble_retriever"]["weights"]:
    f_avg.write(f'{tabSpacer(weight)}')
    for top_k in test_vars["ensemble_retriever"]["top_k"]:
        print(f"top_k:{top_k}, Weight: {weight}")
        f_indiv = open(
            f"{curr_path}/individual_results/weight{weight}_topk{top_k}.txt", "w")
        f_indiv.write(
            f"{tabSpacer('doc_idx')}|{tabSpacer('recall')}|{tabSpacer('precision')}|{tabSpacer('fscore')}\n")

        list_fscore = []

        for i, x in enumerate(test_vars["payload"]):
            retrieved_docs = search2.search(
                x["query"], weight=weight, top_n=top_k)
            total_retrieved, relevant_retrieved = 0, 0
            total_relevant = len(x["relavant"])
            for doc in retrieved_docs:
                idx = f"{doc.metadata['relative_path']},{doc.metadata['start_offset']},{doc.metadata['end_offset']}"
                if idx in x["relavant"]:
                    relevant_retrieved += 1
                total_retrieved += 1
            if relevant_retrieved == 0:
                recall = 0
                precision = 0
                fscore = 0
            else:
                recall = relevant_retrieved/total_relevant
                precision = relevant_retrieved/total_retrieved
                fscore = (2*precision*recall)/(precision+recall)
            list_fscore.append(fscore)
            f_indiv.write(
                f"{tabSpacer(i)}|{tabSpacer(recall)}|{tabSpacer(precision)}|{tabSpacer(fscore)}\n")
        f_indiv.close()
        avg_fscore = np.average(list_fscore)
        f_avg.write("|"+tabSpacer(avg_fscore))
    f_avg.write("\n")
f_avg.close()
