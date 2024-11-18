import tree_sitter_python as tspython
from tree_sitter import Language, Node, Parser 
import sys
import os 
from typing import List, Dict
from pprint import pprint
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

py_mapping = {
    "function_definition": "function",
    "class_definition": "class",
    "module": "root"
}

def extract_nodes(node: Node, source_code: bytes, parent_type: str = "root", parent_name: str = ""):
    def get_node_text(node: Node) -> str:
        """
        Helper function to get the text of a node from the source code, from its start and end bytes
        """
        return source_code[node.start_byte: node.end_byte].decode()

    def extract_function_details(node: Node, parent_name: str):
        """
        Helper function to extract function details
        """
        # Get function name
        node_name = node.child_by_field_name("name")
        if node_name is None: return None
        function_name = get_node_text(node_name)

        # Get function parameters
        arguments = []
        node_params = node.child_by_field_name("parameters")
        if node_params is None:
            return None

        node_params = node_params.children
        for arg in node_params:
            if arg.type == "identifier":
                if arg.text is not None:
                    arguments.append(arg.text.decode("utf8"))

        # Get return variable
        return_variable = None
        for child in node.children:
            if child.type == 'return_statement':
                # Capture the expression being returned
                return_expr = child.children[0] if child.children else None
                if return_expr:
                    if return_expr.type == "identifier":  # Simple variable
                        return_variable = get_node_text(return_expr)
                    else:  # More complex expression instead of an easy to read name
                        return_variable = get_node_text(return_expr)  # Keep it as an expression, e.g., `x + y`

        # Find all function calls inside the function
        functions_called = []
        for child in node.children:
            if child.type == "call_expression":  # Function call
                function_calls = child.child_by_field_name("function")
                if function_calls is not None:
                    called_function_name = get_node_text(function_calls)
                    functions_called.append(called_function_name)

        # Extract docstrings and comments
        docstrings = []
        for child in node.children:
            if child.type == "string":
                docstrings.append(get_node_text(child))

        return {
            "start_offset": node.start_byte,
            "end_offset": node.end_byte,
            "block_type": "function",
            "block_name": function_name,
            "block_args": arguments,
            "parent_type": parent_type,
            "parent_name": parent_name,
            "return_var_ast": return_variable,
            "functions_called": functions_called,
            "docstrings": docstrings
        }

    # Helper function to extract class details
    def extract_class_details(node: Node, parent_name: str):

        node_name = node.child_by_field_name("name")
        if node_name is None:
            return None
        class_name = get_node_text(node_name)

        # Find methods in the class
        methods = []
        for child in node.children:
            if child.type == "function_definition":
                methods.append(extract_function_details(child, class_name))

        # Extract docstrings and comments
        docstrings = []
        for child in node.children:
            if child.type == "string":
                docstrings.append(get_node_text(child))

        # Extracting block_args from __init__  instead 
        block_args = []
        for method in methods:
            init_args = method.get("block_args")
            if init_args:
                block_args = init_args

        return {
            "start_offset": node.start_byte,
            "end_offset": node.end_byte,
            "block_type": "class",
            "block_name": class_name,
            "block_args": block_args, # Classes don't have arguments like functions. This is instead captured in the __init__ method
            "parent_type": parent_type,
            "parent_name": parent_name,
            "methods": methods,   # TODO: Might be too verbose
            "docstrings": docstrings
        }

    # Default block: handle other non-class and non-function blocks in global score (e.g if, with, for etc.)
    def extract_other_details(node: Node, parent_name: str):
        functions_called = []

        # Find any function calls inside this block
        for child in node.children:
            if child.type == "call_expression":  # Function call in the block
                function_calls = child.child_by_field_name("function")
                if function_calls is not None:
                    called_function_name = get_node_text(function_calls)
                    functions_called.append(called_function_name)

        # Extract docstrings and comments
        docstrings = []
        for child in node.children:
            if child.type == "string":
                docstrings.append(get_node_text(child))

        return {
            "start_offset": node.start_byte,
            "end_offset": node.end_byte,
            "block_type": "others",
            "block_name": f"Block at {node.start_byte}-{node.end_byte}",  # Generic block name 
            "block_args": [],  # No arguments for "others" blocks
            "parent_type": parent_type,
            "parent_name": parent_name,
            "functions_called": functions_called,
            "docstrings": docstrings
        }

    result = []
    curr_name = ""  # Current name is the next node's parent name

    # For current node - process and add to result
    match node.type:
        case "function_definition":
            details = extract_function_details(node, parent_name)
            if details is not None:
                curr_name = details["block_name"]
                result.append(details)
        case "class_definition":
            details = extract_class_details(node, parent_name)
            if details is not None:
                curr_name = details["block_name"]
                result.append(details)
        case _:  # For non-function or non-class types, base case
            details = extract_other_details(node, parent_name)
            if details is not None:
                curr_name = details["block_name"]
                result.append(details)

    # Base case for DFS recursion: Stop if the node has no children
    if not node.children:
        return result

    # For child nodes - Recursively process all child nodes via DFS strategy, but only for relevant nodes
    for child in node.children:
        if child.type in ["function_definition", "class_definition"]:  # Only recurse on functions and classes
            result.extend(extract_nodes(child, source_code, parent_type=py_mapping[node.type], parent_name=curr_name))
        else:  # For non-relevant blocks, just extract their metadata (no further recursion)
            result.append(extract_other_details(child, curr_name))

    # Sort by byte offset to ensure correct order
    result.sort(key=lambda x: x.get("start_byte", 0))

    return result

def merge_others_metadata(node_metadata: List[Dict]):
    """
    Given a list of dictionary of metadata - extracts all "others" node types and merges them, 
    replacing any parts of the code where classes and functions were with "Code for: <func/class info>"
    """
    return
    
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
    # pprint(ASTGeneratedMetadata.model_json_schema())
    all_nodes = extract_nodes(tree.root_node, test_code, "root", "")
    pprint(all_nodes)
    for i, node in enumerate(all_nodes):
        print(i)
        if node["parent_name"] == "Person":
            print(test_code[node['start_offset']:node['end_offset']])

if __name__ == "__main__":
    main()
