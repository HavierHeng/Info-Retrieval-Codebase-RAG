from pydantic import BaseModel, Field
from typing import Literal, List

class CodeSummary(BaseModel):
    type: str

class LLMGeneratedMetadata(BaseModel):
    """
    Returns the blank schema for Lagnchain MetadataTagger to fill in via LLM. This is used to generate some parts of the metadata that cannot be made just by Langchain alone.

    Some of these fields are redundant, and already detected by AST. This is just kept as a potential use for cross validation.
    """
    block_type: str  # Type of block. Others block will contain simplified code for other blocks through commenting. Either class/method/function/others
    block_name:  str # name of block e.g class name, function name
    return_var_name:  str   # Return variable name if clearcut
    functions_called: List[str]  # List of functions called
    docstrings: List[str]  # List of codestrings
    code_summary: CodeSummary  #  Code summary


class CodeDocumentMetadata(BaseModel):
    """
    Returns the schema for any generic code document.
    """
    relative_path: str  # Path to source file relative to project base directory
    start_offset: int  # Start byte offset of block in source code
    end_offset: int  # End byte offset of block in source code


class ASTGeneratedMetadata(BaseModel):
    """
    Returns the schema returned only by the AST part of the Document Loader. This is for reference only, not really needed to be called.
    """
    code_metadata: CodeDocumentMetadata

    # AST generated blocks
    block_name: str  # Name of block e.g class, function, method names
    block_type: str  # Type of block. Others block will contain simplified code for other blocks through commenting. Either class/method/function/others
    parent_type: str  # Parent block. Either root/class
    functions_called: list[str]   # list of functions called
    docstrings: list[str]  # list of docstrings
    summary: str  # llm generated summary


class FullCodeDocumentMetadata(BaseModel):
    """
    The DocumentLoader returns full metadata in the following schema, for use for general retrieval tasking (e.g contextual) or retrieval of citations (using paths and start/end offsets). 
    """
    ast_generated: ASTGeneratedMetadata
    llm_generated: LLMGeneratedMetadata
