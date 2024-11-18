# Reference for Langchain BaseLoader: https://python.langchain.com/docs/how_to/document_loader_custom/
# Refernce for Treesitter-Python: https://github.com/tree-sitter/tree-sitter-python/tree/master

import tree_sitter_python as tspython
from tree_sitter import Language, Parser
from typing import AsyncIterable, Iterator, Union, Optional, List
from pathlib import Path
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document
from langchain_text_splitters import TextSplitter
from metadata_schema.metadata_schema import ASTGeneratedMetadata  

# TODO: Make this class generic for multiple languages that might share some traits e.g python and javascript and ruby, go and c++, java and C#
python_mapping = {
        "function": "function_definition",
        "async_function": "async_function_definition",
        "class": "class_definition",
        "method": "method_definition",
        "comment": "comment"
}
PY_PARSER = Parser(Language(tspython.language()))


class PythonASTDocumentLoader(BaseLoader):
    """
    A smarter version of PythonLoader that uses Treesitter to parse its abstract syntax trees, and return Document objects that contain blocks (defined by functions or classes or any other structures).

    Non-function/non-class blocks are categorized seperately.

    Document objects contain metadata for use in retrieval tasks and pipelines.
    """
    def __init__(self, file_path: Union[str, Path], parser: Parser):
        """
        Initialize loader with a file path containg code.
        """
        self.file_path = file_path
        self.parser = parser

    def lazy_load(self) -> Iterator[Document]:
        """
        A lazy loader that reads code file code block by code block.
        Yield documents representing a code block one by one.
        """
        with open(self.file_path, encoding="utf-8") as f:
            if self._is_valid(f.read()):
                f.seek(0)  # return offset to beginning
            else:
                print(f"Invalid code type {self.file_path}")
                return None

        with open(self.file_path, encoding="utf-8") as f:
            # TODO: Get all possible blocks
            # Combine all others blocks - throw into simplify_code
            # TODO: Generate metadata for each block, this might need to explore local llm as well
            # yield each document, add lines

            yield Document(
                page_content = code_content,
                metadata = {}
            )

    def _is_valid(self, code) -> bool:
        """
        Checks if code is parsable by treesitter.
        """
        return self.parser.parse(code) is not None

    def _generate_metadata(self):
        """
        Given a metadata code block, generate info about it.
        """
        ast_metadata = ASTGeneratedMetadata()

        return ast_metadata

    def _extract_block_offsets(self, mapping) -> List[Tuple[int, int]]:
        """
        Returns as a sorted list of tuples containing the start and end offset of the block. 
        """

        tree = tspython.
        start_offset, end_offset = (0, 10)
        offsets = [(start_offset, end_offset) for i in range(10)]
        return sorted(offsets, key: lambda x: x[0])

    def _simplify_code(self, block_offsets, text_splitter: Optional[TextSplitter] = None):
        """
        For all blocks in the block offsets, extracts block types, either class/method/function/others. 

        For code blocks with no categorization, e.g when they just sit in the global scope, these will be combined into one huge document. These block will contain simplified code for other blocks through commenting.

        Example - for code block with "others" tag - "Code for: xx "
        ----------------------------------------------------------
        # Code for: def read_file(file_name):

        # Write some text to a file
        with open('sample.txt', 'w') as f:
            f.write("Hello, world!\nThis is a test file.")

        # Call the function to read and print the file contents
        read_file('sample.txt')

        # Create a simple list and calculate the sum
        numbers = [1, 2, 3, 4, 5]
        total = sum(numbers)
        print(f"Sum of numbers: {total}")
        """
        if text_splitter is not None:
            splitter = text_splitter(chunk_size=256,
                                     chunk_overlap=16)
            return splitter.split_text()
        return

    def _extract_block_metadata(self):
        return

   


