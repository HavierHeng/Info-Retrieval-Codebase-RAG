import tree_sitter_python as tspython
from tree_sitter import Language, Node, Parser, TreeCursor
from functools import partial
from typing import Optional
import sys
import os 
from pprint import pprint

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
"""
 'required': ['relative_path',
              'start_offset',
              'end_offset',
              'block_type',
              'block_name',
              'block_args',
              'parent_type',
              'parent_name',
              'return_var_ast',
              'functions_called',
              'docstrings',
"""

from metadata_schema.metadata_schema import ASTGeneratedMetadata

def get_func_class_names(node: Node, original: str) -> Optional[str]:
    # Given a cursor which is one a node of interest
    return

def get_methods_of_class(node: Node, original: str) -> Optional[str]:
    # Gets all info about the methods of a class
    return

def get_root_node_children(tree):
    root_node = tree.root_node
    return root_node.children

def simplify_code(tree, source_code):
    result = {}
    others = [] 
    for node in get_root_node_children(tree):
        match node.type:
            case "function_definition":
                name = get_func_class_names(node, source_code)
                result[f"{node.type} {name}"] = (node.start_byte, node.end_byte, source_code[node.start_byte : node.end_byte].decode())
                others.append(f"# Code for: {name}")
            case "class_definition":
                name = get_func_class_names(node, source_code)
                get_methods_of_class(node, source_code)
                result[f"{node.type} {name}"] = (node.start_byte, node.end_byte, source_code[node.start_byte : node.end_byte].decode())
                others.append(f"# Code for: {name}")
            case "comment":
                result[f"{node.type}"] = (node.start_byte, node.end_byte, source_code[node.start_byte : node.end_byte].decode())
            case _:
                print(node.type)
                others.append(source_code[node.start_byte : node.end_byte].decode())
        
    result["others"] = "\n".join(others)  
    return result

def main():
    # In treesitter, a Parser is used to make a Tree
    # Parser is to be defined per language
    py_language = Language(tspython.language())
    parser = Parser(py_language)
    test_code = bytes(""" 
import random
import asyncio
def read_file(file_name):
    with open(file_name, 'r') as f:
        return f.read()

# Write some text to a file
with open('sample.txt', 'w') as f:
    f.write("Hello, world!\nThis is a test file.")

# Call the function to read and print the file contents
read_file('sample.txt')

# Create a simple list and calculate the sum
numbers = [1, 2, 3, 4, 5]
total = sum(numbers)
print(f"Sum of numbers: {total}")

def test_print(who, two, three, *args, **kwargs):
    print(who)

class Person:
    ''' 
    Defines a person - Docstring
    ''' 
    SURPRISE = "SURPRISE"
    def __init__(self, name):
        # Init - standalone comment
        self.name = name

    def intro(self):
        print("I am", self.name)  # Greet someone - Inline comment

    def curse(self, target):

        def random_curse(self):
            return random.choice(["idiot", "dumbass", "fool"])

        return "".join([target, "you", random_curse()])

async def count():
    print("One")
    await asyncio.sleep(1)
    print("Two")

tomas = Person("tomathy")
tomas.intro()
""", "utf8")
    tree = parser.parse(test_code)
    pprint(ASTGeneratedMetadata.model_json_schema())

if __name__ == "__main__":
    main()
