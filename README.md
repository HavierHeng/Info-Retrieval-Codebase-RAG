# SUTD Information Retrieval Project - Github Codebase RAG 


## Description

# Setup

## Hardware requirements

The assumption is that your device has a Nvidia GPU with the appropriate CUDA 12 drivers. 
This is needed for the LLM and FAISS and other parts of the project.

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
