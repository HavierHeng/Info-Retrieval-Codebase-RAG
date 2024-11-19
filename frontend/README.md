# Frontend for RAG system

## Description

The frontend provides a simple chatbot interface to the RAG system to query about a codebase.

## Setup

## Hardware requirement

Nvidia GPU only... CUDA doesn't work otherwise. 

## Pre-Requisites 

You should have Python 3 installed before using this tokenizer. Verify this with either:
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
3) Install dependencies - `pip install -r requirements.txt`
## Execution
Run Streamlit with: `streamlit run chatbot.py`
