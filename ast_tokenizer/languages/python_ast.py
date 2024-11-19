# Reference for Langchain BaseLoader: https://python.langchain.com/docs/how_to/document_loader_custom/
# Refernce for Treesitter-Python: https://github.com/tree-sitter/tree-sitter-python/tree/master

import tree_sitter_python as tspython
from tree_sitter import Language, Node, Parser
from typing import Iterator, Union, Optional, List, Dict, Tuple
from pathlib import Path
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import langchain_text_splitters

PYLANGUAGE = Language(tspython.language())
PY_PARSER = Parser(PYLANGUAGE)

py_mapping = {
    "function_definition": "function",
    "class_definition": "class",
    "module": "root"
}

class PythonASTDocumentLoader(BaseLoader):
    """
    A smarter version of PythonLoader that uses Treesitter to parse its abstract syntax trees, and return Document objects that contain blocks (defined by functions or classes or any other structures).

    Non-function/non-class blocks are categorized seperately.

    Document objects contain metadata for use in retrieval tasks and pipelines.
    """
    def __init__(self, file_path: Union[str, Path]):
        """
        Initialize loader with a file path containg code.
        """
        self.file_path = file_path

    def lazy_load(self) -> Iterator[Document]:
        """
        A lazy loader that reads code file code block by code block.
        Yield documents representing a code block one by one.
        """
        with open(self.file_path, "rb") as f:
            code_file_bytes = f.read()
            tree = PY_PARSER.parse(code_file_bytes)
            all_nodes_metadata = self.__extract_nodes(tree.root_node, code_file_bytes, "root", "")
            # all_nodes_text = [code_file_bytes[node["start_offset"]:node["end_offset"]].decode() for node in all_nodes_metadata]
            all_nodes_text, all_nodes_metadata = self.__simplify_metadata(all_nodes_metadata, code_file_bytes)  
            # all_nodes_text.extend(combined_others_text)
            # all_nodes_metadata.extend(combined_others_metadata)

            # TODO: Generate remaining metadata for each block using LLM - Pydantic

            for node_text, node_metadata in zip(all_nodes_text, all_nodes_metadata):
                yield Document(
                    page_content = node_text,
                    metadata = node_metadata 
                )

    def __extract_nodes(self, node: Node, source_code: bytes, parent_type: str = "root", parent_name: str = ""):
        def get_node_text(node: Node) -> str:
            """
            Helper function to get the text of a node from the source code, from its start and end bytes
            """
            return source_code[node.start_byte: node.end_byte].decode()

        def extract_function_calls(node: Node):
            """
            Helper function to extract all docstrings and comments from the source code, from its start and end bytes
            """
            query = PYLANGUAGE.query("""
                (call) @function_call
            """)

            captures = query.captures(node)

            function_calls = []
            if captures.get("function_call") is not None:
                for node in captures["function_call"]:
                    function_call_text = source_code[node.start_byte:node.end_byte].decode()
                    function_calls.append(function_call_text)

            return function_calls 

        def extract_comments_docstrings(node: Node):
            """
            Helper function to extract all docstrings and comments from the source code, from its start and end bytes
            """
            def strip_single_line_comments(text: str):
                # Strip the comment if it starts with "# "
                if text.strip().startswith("#"):
                    return text.lstrip("#").strip()  # Remove the "# " and any leading/trailing spaces
                return text

            def strip_docstring(text: str):
                if text.startswith('"""') and text.endswith('"""'):
                    return text[3:-3].strip()  # Remove the surrounding triple quotes
                return text

            # Define a query to capture both line and block comments
            query = PYLANGUAGE.query("""
                (comment) @comment
                (expression_statement (string) @docstring)
            """)

            # Run the query on the node
            captures = query.captures(node)

            comments = []
            if captures.get("comment") is not None:
                for node in captures["comment"]:
                    comment_text = source_code[node.start_byte:node.end_byte].decode()
                    comments.append(strip_single_line_comments(comment_text))

            docstrings = []
            if captures.get("docstring") is not None:
                for node in captures["docstring"]:
                    docstring_text = source_code[node.start_byte:node.end_byte].decode()
                    docstrings.append(strip_docstring(docstring_text))

            return comments, docstrings

        def extract_function_details(node: Node, parent_name: str):
            """
            Helper function to extract function details
            """
            # Get function name
            node_name = node.child_by_field_name("name")
            if node_name is None: 
                return None
            function_name = get_node_text(node_name)

            # Get function parameters
            arguments = []
            node_params = node.child_by_field_name("parameters")
            if node_params is not None:
                node_params = node_params.children
                for arg in node_params:
                    if arg.type == "identifier":
                        if arg.text is not None:
                            arguments.append(arg.text.decode())

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
            functions_called = extract_function_calls(node)

            # Extract docstrings and comments
            comments, docstrings = extract_comments_docstrings(node)

            return {
                "relative_path": self.file_path,
                "start_offset": node.start_byte,
                "end_offset": node.end_byte,
                "block_type": "function",
                "block_name": function_name,
                "block_args": arguments,
                "parent_type": parent_type,
                "parent_name": parent_name,
                "return_var_ast": return_variable,
                "functions_called": functions_called,
                "docstrings": docstrings,
                "comments": comments 
            }

        # Helper function to extract class details
        def extract_class_details(node: Node, parent_name: str):
            node_name = node.child_by_field_name("name")
            if node_name is None:
                return None
            class_name = get_node_text(node_name)

            # Find methods in the class
            methods = []
            node_body = node.child_by_field_name("body")
            if node_body is not None:
                for child in node_body.children:
                    if child.type == "function_definition":
                        methods.append(extract_function_details(child, class_name))

            # Extract docstrings and comments
            comments, docstrings = extract_comments_docstrings(node)
            
            # Extracting block_args from __init__  instead 
            block_args = []
            for method in methods:
                init_args = method.get("block_args")
                if init_args:
                    block_args = init_args

            return {
                "relative_path": self.file_path,
                "start_offset": node.start_byte,
                "end_offset": node.end_byte,
                "block_type": "class",
                "block_name": class_name,
                "block_args": block_args, # Classes don't have arguments like functions. This is instead captured in the __init__ method
                "parent_type": parent_type,
                "parent_name": parent_name,
                "methods": methods,   # TODO: Might be too verbose
                "docstrings": docstrings,
                "comments": comments
            }

        # Default block: handle other non-class and non-function blocks in global score (e.g if, with, for etc.)
        def extract_other_details(node: Node, parent_name: str):
            functions_called = []

            # Find any function calls inside this block
            functions_called = extract_function_calls(node)

            # Extract docstrings and comments
            comments, docstrings = extract_comments_docstrings(node)

            return {
                "relative_path": self.file_path,
                "start_offset": node.start_byte,
                "end_offset": node.end_byte,
                "block_type": "others",
                "block_name": f"Block at {node.start_byte}-{node.end_byte}",  # Generic block name 
                "block_args": [],  # No arguments for "others" blocks
                "parent_type": parent_type,
                "parent_name": parent_name,
                "functions_called": functions_called,
                "docstrings": docstrings,
                "comments": comments
            }

        result = []
        curr_name = ""  # Current name is the next node's parent name
        processed = set()  # DFS - Prevent reprocessing of nodes. 

        # Base case for DFS recursion: Stop if the node has no children. 
        if not node.children:
            return result

        def process_node(node):
            # Skip root node from being processed as 'others'
            if py_mapping[node.type] == "root":
                return None

            # For current node - process and add to result if not already processed
            if node in processed:
                return None  # Skip node from reprocessing

            # Add node otherwise - and process
            processed.add(node)

            match node.type:
                case "function_definition":
                    details = extract_function_details(node, parent_name)
                    if details is not None:
                        return details
                case "class_definition":
                    details = extract_class_details(node, parent_name)
                    if details is not None:
                        return details
                case _:  # For non-function or non-class types, base case
                    details = extract_other_details(node, parent_name)
                    if details is not None:
                        return details
            return None

        # Process current node and add to result
        details = process_node(node)
        if details is not None:
            curr_name = details["block_name"]
            result.append(details)

        # For child nodes - Recursively process all child nodes via DFS strategy, but only for relevant nodes
        for child in node.children:
            if child.type in ["function_definition", "class_definition"]:  # Only recurse on functions and classes
                result.extend(self.__extract_nodes(child, source_code, parent_type=py_mapping[node.type], parent_name=curr_name))
            else:  # For non-relevant blocks, just extract their metadata (no further recursion)
                # Check if current node is not a function or class
                if node.type not in ["function_definition", "class_definition"]:
                    result.append(extract_other_details(child, curr_name))

        # Sort by byte offset to ensure correct order
        result.sort(key=lambda x: x.get("start_offset", 0))

        return result

    def __simplify_metadata(
        self,
        nodes_metadata: List[Dict],
        source_code: bytes,
        text_splitter: Optional[RecursiveCharacterTextSplitter] = None
    ) -> Tuple[List[str], List[Dict]]:
        """
        Given a list of dictionary of metadata - extracts all "others" node types and merges their code. 
        "others" node types represent code blocks with no categorization, e.g when they just sit in the global scope, 
        these will be combined into one huge document. These blocks will contain simplified code for other blocks through commenting.

        Any parts of the code where classes and functions were are replaced with "Code for: <func/class info>"
        
        If a RecursiveCharacterTextSplitter is provided, it will be used to split the huge "others" block.

        All other classes/function blocks are kept in order.

        PS: This class is pretty much the messy part of the code - its just formatting.
        """
        if len(nodes_metadata) == 0:
            return [], []

        all_nodes = []
        others = []
        others_metadata = {
            "relative_path": self.file_path,
            "start_offset": nodes_metadata[0].get("start_offset"),
            "end_offset": nodes_metadata[-1].get("end_offset"),
            "block_type": "others",
            "block_name": "Combined Others",  # Generic block name 
            "block_args": [],  # No arguments for "others" blocks
            "parent_type": "root",
            "parent_name": "root",
            "functions_called": [],
            "docstrings": [],
            "comments": []
        }

        # Sort nodes by their start offset if not already sorted
        nodes_metadata.sort(key=lambda x: x.get("start_offset", 0))

        # Gather all function/class nodes code blocks as bytes - this is to setup to inject in "Code for: " statements
        all_nodes_text = [] 

        for node_data in nodes_metadata:
            match node_data["block_type"]:
                case "others":  # Merge code
                    # Append all functions and comments - so as to save on processing
                    for key in ["functions_called", "docstrings", "comments"]:
                        others_metadata[key] = others_metadata.get(key, []) + node_data.get(key, [])
                    others.append(source_code[node_data["start_offset"]: node_data["end_offset"]] + b'\n')
                case "function":
                    args = ", ".join(node_data["block_args"])
                    all_nodes.append(node_data)
                    others.append(f"# Code for {node_data['block_type']}: {node_data['block_name']}({args})\n".encode())
                case "class":
                    args = ", ".join(node_data["block_args"])
                    others.append(f"# Code for {node_data['block_type']}: {node_data['block_name']}({args})\n".encode())

                    # Set the end point of class as the start point of the first method if any
                    node_methods = node_data.get("methods", None)
                    if node_methods:
                        node_data["end_offset"] = node_methods[0]["start_offset"]

                    # Add node text
                    node_text = [source_code[node_data["start_offset"]: node_data["end_offset"]]]

                    # All method separately as its own entry
                    for node_method in node_methods: 
                        # Add node methods as their own standalone entry
                        all_nodes.append(node_method)
                        all_nodes_text.append(source_code[node_method["start_offset"]: node_method["end_offset"]])

                        args = ", ".join(node_method["block_args"])
                        # For adding to classes
                        node_text.append(f"# Code for {node_method['block_type']}: {node_data['block_name']}.{node_method['block_name']}({args})\n".encode())

                        # For adding to combined others block
                        others.append(f"# Code for {node_method['block_type']}: {node_data['block_name']}.{node_method['block_name']}({args})\n".encode())

                    all_nodes.append(node_data)
                    all_nodes_text.append(b"".join(node_text).decode())


        # Merge all code blocks into one document
        others_doc = b"".join(others)
        others_doc_text = others_doc.decode()

        # Use the text splitter if provided
        if text_splitter is not None:
            if isinstance(text_splitter, type):  # if it's a class, instantiate a standard splitter
                splitter = text_splitter.from_language(language=langchain_text_splitters.Language.PYTHON,
                                                       chunk_size=256,
                                                       chunk_overlap=16)
            else:
                splitter = text_splitter  # if it's an instance, use it as is

            others_doc_text = splitter.split_text(others_doc_text)
            others_metadata = [others_metadata for _ in range(len(others_doc_text))]  # Naively clone metadata for now
        else:
            others_doc_text = [others_doc_text]
            others_metadata = [others_metadata]

        all_nodes.extend(others_metadata)
        all_nodes_text.extend(others_doc_text)

        sorted_nodes = sorted(zip(all_nodes_text, all_nodes), key=lambda x: x[1]["start_offset"])
        all_nodes_text, all_nodes = zip(*sorted_nodes)

        return all_nodes_text, all_nodes
