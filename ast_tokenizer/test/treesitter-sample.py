import tree_sitter_python as tspython
from tree_sitter import Language, Node, Parser, TreeCursor
from functools import partial
from typing import Optional

def read_callable_byte_offset(src, byte_offset, _):
    # Example: Only use byte_offset in the callback return src[byte_offset : byte_offset + 1]
    return src[byte_offset: byte_offset + 1]

def read_callable_point(src_lines, _, point):
    # Example: Use point in callback which represents a row, column position of a byte
    # src_lines is an array of lines
    row, column = point
    if row >= len(src_lines) or column >= len(src_lines[row]):
        return None
    return src_lines[row][column:]

def get_func_class_names(node: Node, original: str) -> Optional[str]:
    # Given a cursor which is one a node of interest
    # Step into each direct child

    cursor = node.walk()
    # Note: cursor.node.walk() segfaults if i use node.walk() outside of the function - likely cos the original node went out of scope in C, so it got dealloc?
    result = None
    if cursor.node is not None:
        if cursor.node.type == "function_definition" or cursor.node.type == "class_definition":
            cursor.goto_first_child()  # `async` or `def` or `class` keyword

            if original[cursor.node.start_byte:cursor.node.end_byte] == b"async":  # async, move one more
                cursor.goto_next_sibling()  

            cursor.goto_next_sibling()  # name of function or class
            result = original[cursor.node.start_byte:cursor.node.end_byte]
    return result

def get_methods_of_class(node: Node, original: str) -> Optional[str]:
    # Gets all info about the methods of a class
    if node.type == "class_definition":
        child_node = node.child_by_field_name("body")
        if child_node is not None:
            cursor = child_node.walk()
            cursor.goto_first_child()
            if cursor.node is not None:
                print(cursor.node.type, cursor.node, original[cursor.node.start_byte:cursor.node.end_byte])
        

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
    test_code_lines = test_code.splitlines()
    # Simple example - directly pass in bytes object
    tree_1 = parser.parse(test_code)

    # Intermediate example - read callable to parse function
    readable_code_bytes = partial(read_callable_byte_offset, test_code)
    tree_2 = parser.parse(readable_code_bytes, encoding="utf8")

    # Intermediate example - using the point which represents a row and column
    # For most files, its easier to use bytes offset. This is more in case its used for text editing
    readable_code_point = partial(read_callable_point, test_code_lines)
    tree_3 = parser.parse(readable_code_point, encoding="utf8")

    # Harder example: mess with navigating the tree
    
    # Treesitter works by Trees with contains Nodes. If memory efficiency is required, use walk() to create a TreeCursor

    # In general, Nodes are not accessed directly... 
    root_node_children = get_root_node_children(tree_1)
    #for child in root_node_children:  # each of these a Node
    #    print(child.type, child.start_byte, child.end_byte, test_code[child.start_byte:child.end_byte])

    # Cursors have to be worked with carefully, as they are pointers, and can segfault if abused.

    for k, v in simplify_code(tree_2, test_code).items():
        print(k)
        print(v)
        print()

if __name__ == "__main__":
    main()
