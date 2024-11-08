# Frontend for RAG system

## Description

The frontend provides a simple chatbot interface to the RAG system to query about a codebase.

## Setup

## Pre-Requisites 

You should have Python 3 installed before using this tokenizer. Verify this with either:
- `python --version`
- `python3 --version`

The project is set up in a virtualenv (`venv`)
1) Activate the virtualenv: 
    - Windows: `frontend/bin/activate` or `frontend/bin/activate.ps1` if in powershell
    - Linux/MacOS (based on shell): `source frontend/bin/activate.sh`
2) Check that environment is activated - terminal prompt should show something like
```
(frontend) $
```
3) Install dependencies - `pip install -r requirements.txt`

## Execution
Run Streamlit with: `streamlit run chatbot.py`
