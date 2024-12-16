from pydantic import BaseModel, Field
from typing import List

# Note to use pydantic - its quite a specific setup
# Pydantic V1 is to be used if using old langchain
# Pydantic V2 is to be used if >0.3 release
# Update Ollama Python package to latest
# Also small models tend to mess up when it comes to Ollama
class Citation(BaseModel):
    """
    Full citation with numebering that acts as a reference for how the answer was generated.
    """
    source_id: int = Field(description="The integer IDs of the SPECIFIC sources which justify the answer.")
    quote: str = Field(description="The VERBATIM quote from the specified source that justifies the answer.")

class InlineAnswer(BaseModel):
    """
    Part of the full answer to the user question citing based on the given sources.
    """
    answer: str = Field(description="The answer to the user question, which is based only on the given sources.")
    source_id: List[int] = Field(description="The integer IDs of the SPECIFIC sources which justify this part of the answer.")

class CitedAnswer(BaseModel):
    """
    Answer the user question based only on the given sources, and cite the sources used.
    """
    answers: List[InlineAnswer] = Field(description="Answers to the user question, based on the given sources in the context")
    citations: List[Citation] = Field(description="Final kept citations from the given sources that are used to justify the answer.")

