# RAG Codebase

## Description

Bulk of the implementation of the RAG system using Langchain to build a custom retrieval pipeline with BM25 and LLM embedding models.

## Design

### Base design

`FAISS` is used to store dense vector embeddings. TF-IDF index is built and stored using `rank_bm25`. These are wrapped up nicely by Langchain to build our RAG system.

### Preprocessing Code Blocks as documents via Abstract Syntax Tree

The hypothesis was to tokenize the input source code into metadata that sufficiently represents the codebase, by picking key class, function, argument, return values and docstrings that explain what the code is doing. This reduces the token cost when sending to an LLM, but also makes the retrieval process aware of the syntax of the code - since code is organized by blocks rather than nearby lines.

An Abstract Syntax Tree based parser is used - and code blocks are identified and isolated as a document to be indexed into the RAG pipelien.
- e.g: a class named `Foo` is a document
- e.g 2: a function named `Bar` is a document on its own

### Hybrid Retrieval Models - using Embedding Models with BM25

This is implemented by a custom retriever that uses both an embedding model and BM25 results. 

Rank fusion is then performed to combine the retrieved data from both streams defined by the formula:

$$RRF(d) = \sum_{r ∈ R} 1 / (k + r(d))$$
where 
- d is a document
- R is the set of rankers
- k is a constant
- r(d) is the rank of a document d in ranker r

This then creates the true final ranking value considering both types of retrieval methods (Embeddings and BM25).

## Setup
### Pre-requisites

Preferred approach is to use a `conda` environment and a Jupyter Notebook.
1) Install `conda` or `anaconda` on your device
2) Create an environment named `rag-codebase` with the necessary packages: `conda env create -f environment.yml` 
3) Install a new kernel: `python -m ipykernel install --user --name=rag-codebase --display-name "RAG Kernel"`

### Execution
Either:
- Activate the conda environment with `conda activate rag-codebase`
- Start Jupyter notebook with `jupyter notebook` - change the kernel to the `rag-codebase` kernel.

### Updating dependencies and libraries
1) Preference is to activate the environment with `conda activate rag-codebase`, just in case `pip install` is called
2) `conda install <package>` or `pip install <package>` 
    - Some packages cannot be found on conda channels alone - e.g `rank_bm25`
3) Update the `environment.yml` file with `conda env export --name rag-codebase > environment.yml`.
