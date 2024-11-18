# Source for python treesitter nodes: https://github.com/tree-sitter/tree-sitter-python/tree/master

import tree_sitter_python as tspython
from tree_sitter import Language, Parser
from typing import AsyncIterable, Iterator, Union 
from pathlib import Path
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document
from metadata.ast_metadata_schema import 


# TODO: Make this class generic for multiple languages that might share some traits e.g python and javascript and ruby, go and c++, java and C#
mapping = {
        "function": "function_definition",
        "class": "class_definition",
        "method": "method_definition",
        "type_def": "type_alias_declaration"
    }

PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)

class PythonASTDocumentLoader(BaseLoader):
    """
    A smarter version of PythonLoader that uses Treesitter to parse its abstract syntax trees, and return Document objects that contain blocks (defined by functions or classes or any other structures). 

    Non-function/classes blocks are categorized seperately.
    """

    
    def __init__(self, file_path: Union[str, Path]):
        """
        Initialize with a file path containg code.
        """
        self.file_path = file_path

    def _generate_metadata(self):
        return

    def _simplify
   

# def read_callable_byte_offset(byte_offset, point):
    return src[byte_offset : byte_offset + 1]


def read_callable_point(byte_offset, point):
    row, column = point
    if row >= len(src_lines) or column >= len(src_lines[row]):
        return None
    return src_lines[row][column:].encode("utf8")


def tokenize_blocks_from_root(tree, original):
    cursor = tree.walk()
    cursor.goto_first_child()
    counter = 1

    # Print the first block
    print(f"\n ---------- BLOCK {counter} ---------- \n", original[cursor.node.start_byte: cursor.node.end_byte])
    print_func_class_names(cursor, original)  
    counter += 1

    while cursor.goto_next_sibling():  # Continue until there are no more siblings
        print(f"\n  ----------  BLOCK {counter} ---------- \n", original[cursor.node.start_byte: cursor.node.end_byte])
        print_func_class_names(cursor, original)
        counter += 1

def print_func_class_names(cursor, original):
    # Given a cursor which is the direct child of a root node
    # Step into each direct child
    old_pos = cursor.copy()  # unfortunately copying it too many times causes a seg fault - so we have to just do it one by one
    if cursor.node.type == "function_definition" or cursor.node.type == "class_definition":
        cursor.goto_first_child()  # `def` or `class` keyword
        cursor.goto_next_sibling()  # name of function or class
        print("NAME: ", original[cursor.node.start_byte:cursor.node.end_byte])
    cursor.reset_to(old_pos)  # Shift cursor back

def walk_tree(tree, original):
    cursor = tree.walk()

    assert cursor.node.type == "module"

    assert cursor.goto_first_child()
    assert cursor.node.type == "function_definition"  # foo()

    result = cursor.goto_next_sibling()
    while result:
        result = cursor.goto_next_sibling()  # jump to __name__=="__main__"
    print(original[cursor.node.start_byte: cursor.node.end_byte])

    cursor.goto_first_child()
    cursor.goto_first_child()

    # assert cursor.node.type == "def"

    # Returns `False` because the `def` node has no children
    # assert not cursor.goto_first_child()

    cursor.goto_next_sibling()
    # assert cursor.node.type == "identifier"
    print(cursor.node.start_byte, cursor.node.end_byte, cursor.node.text, original[cursor.node.start_byte: cursor.node.end_byte])

    cursor.goto_next_sibling()
    # assert cursor.node.type == "parameters"

    cursor.goto_parent()

