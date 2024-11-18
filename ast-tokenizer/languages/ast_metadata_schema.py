from pydantic import BaseModel, Field
from typing import Literal, List

class CodeSummary(BaseModel):
    type: str

class LLMGeneratedMetadata(BaseModel):
    """
    Returns the blank schema for Lagnchain MetadataTagger to fill in via LLM. This is used to generate some parts of the metadata that cannot be made just by Langchain alone.
    """
    type: str  # class/method/function/others
    block_name:  str # name of block e.g class name, function name
    return_var_name:  str   # Return variable name if clearcut
    functions_called: List[str]  # List of functions called
    docstrings: List[str]  # List of codestrings
    code_summary: CodeSummary  #  Code summary

class ASTGeneratedMetadata(BaseModel):
    """
    Returns the schema returned only by the AST part of the Document Loader. This is for reference only, not really needed to be called.
    """
    "relative_path": str,  # Path to source file relative to project base directory
    "start_offset": int,  # Start byte offset of block in source code
    "end_offset": int,  # End byte offset of block in source code
    "type": "class/method/function/others",  # Type of block. Others block will contain simplified code for other blocks through commenting.
    "parent_type": "module/class",
    "block_name": "<class/function/method name>",
    "functions_called": list[str],   # list of functions called
    "docstrings": list[str],  # list of docstrings
    "summary": str  # llm generated summary


@staticmethod
def get_full_metadata_schema():
    """
    This DocumentLoader returns metadata in the following schema, for use for general retrieval tasking (e.g contextual) or retrieval of citations (using paths and start/end offsets). 

    This method returns that schema for reference.

    "relative_path": str,  # Relative to the project base directory
    "start_offset": int,  # Start byte offset of block in the source code
    "end_offset": int,  # End byte offset of block in the source code
    "type": "class/method/function/others",  # Type of block. Others blocks will contain simplified code for other blocks as well.
    "parent_type": "root/class",  # Parent if any. Root means that the code just sits in the global namespace
    "block_name": "<class/function/method name>",
    "functions_called": list[str],   # list of functions called
    "docstrings": list[str],  # list of docstrings
    "return_var_name": str,  # Name of return variable if clearcut 
    "summary": str  # llm generated summary
    """

    return {
        "relative_path": str,
        "start_offset": int,
        "end_offset": int,
        "type": "class/method/function/others",
        "parent_type": "module/class",
        "block_name": "<class/function/method name>",
        "functions_called": list[str],   # list of functions called
        "docstrings": list[str],  # list of docstrings
        "summary": str  # llm generated summary
    }

