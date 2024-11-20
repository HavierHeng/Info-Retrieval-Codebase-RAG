# SUTD Information Retrieval Project - Github Codebase RAG 

## Description
This project aims to design a Retrieval Augmented Generation(RAG) system for understanding codebases in large and unfamiliar Git/GitHub repositories, especially when documentation is lacking or incomplete.

The project consists of a Langchain RAG System, a streamlit frontend that has incorporated all the logic from the RAG system, and custom Abstract Syntax Tree (AST) document parser based on treesitter. 

The RAG System runs locally on the host device, using open-source models and embeddings where possible.

# Setup

## Hardware requirements

The assumption is that the device has a Nvidia GPU with the appropriate CUDA 12 drivers. These can be checked via [Pytorch Installation Guide](https://pytorch.org/get-started/locally/).
This is needed to accelerate the LLM, FAISS and other parts of the project.

## Pre-Requisites 

You should have Python 3 installed before this project. Verify this with either:
- `python --version`
- `python3 --version`

The project is set up in a virtualenv (`venv`)
1) Create venv: `python -m venv .venv`
2) Activate the virtualenv: 
    - Windows: `.venv/bin/activate` or `ast-tokenizer/bin/activate.ps1` if in powershell
    - Linux/MacOS (based on shell): `source .venv/bin/activate.sh`
3) Check that environment is activated - terminal prompt should show something like
```
(.venv) $
```
4) Install dependencies - `pip install -r requirements.txt`


## More information
- [Tokenizer](ast_tokenizer/README.md)
- [RAG System](rag-codebase/README.md)
- [Frontend Implementation](frontend/README.md)
