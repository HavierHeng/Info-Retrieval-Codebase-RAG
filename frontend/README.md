# Frontend for RAG system

## Description

The frontend provides a simple chatbot interface to the RAG system to query about a codebase.

# Setup

## Prerequisites
Follow the instructions in the root of the project repo. 
You should install a virtual environment which is to be activated when code is to be run.
Do note that Nvidia GPU with CUDA enabled is required.

1) Activate the virtualenv: 
    - Windows: `.venv/bin/activate` or `ast-tokenizer/bin/activate.ps1` if in powershell
    - Linux/MacOS (based on shell): `source .venv/bin/activate.sh`
2) Check that environment is activated - terminal prompt should show something like
```
(.venv) $
```

## Execution
Run Streamlit with: `streamlit run chatbot.py`
