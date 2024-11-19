import tree_sitter_python as tspython
from tree_sitter import Language, Node, Parser
from typing import Iterator, Union, Optional, List, Dict, Tuple
from pathlib import Path
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import langchain_text_splitters

PY_LANGUAGE = Language(tspython.language())
PY_PARSER = Parser(PY_LANGUAGE)

py_mapping = {
    "function_definition": "function",
    "class_definition": "class",
    "module": "root"
}

class PythonASTDocumentLoader(BaseLoader):
    """
    A smarter version of PythonLoader that uses Treesitter to parse its abstract syntax trees, 
    and return Document objects that contain blocks (defined by functions, classes, or other structures).
    """

    def __init__(self, file_path: Union[str, Path]):
        self.file_path = file_path

    def lazy_load(self) -> Iterator[Document]:
        """
        A lazy loader that reads code file block by block.
        """
        with open(self.file_path, "rb") as f:
            code_file_bytes = f.read()
            self.source_code = code_file_bytes
            tree = PY_PARSER.parse(code_file_bytes)
            all_nodes_metadata = self.__extract_nodes(tree.root_node, code_file_bytes, "root", "")
            all_nodes_text, all_nodes_metadata = self.__simplify_metadata(all_nodes_metadata, code_file_bytes)
            
            for node_text, node_metadata in zip(all_nodes_text, all_nodes_metadata):
                yield Document(page_content=node_text, metadata=node_metadata)

    def __extract_nodes(self, node: Node, source_code: bytes, parent_type: str = "root", parent_name: str = "") -> List[Dict]:
        """
        Extract nodes recursively from the AST and return a list of node metadata.
        """
        def process_node(node):
            """
            Process a node based on its type and return its metadata.
            """
            # Skip root node from being processed
            if py_mapping[node.type] == "root":
                return None

            node_metadata = None
            if node.type == "function_definition":
                node_metadata = self.__extract_function_details(node, parent_name, parent_type)
            elif node.type == "class_definition":
                node_metadata = self.__extract_class_details(node, parent_name, parent_type)
            else:
                node_metadata = self.__extract_other_details(node, parent_name, parent_type)

            return node_metadata

        def process_child_nodes(node, curr_name):
            """
            Process child nodes recursively via DFS strategy based on their type. 
            Functions and classes are recursed, while others blocks are processed as is. Parent name (derived from recursion) and type (derived from the node) are based on the current nodes name and type.
            """
            result = []
            for child in node.children:
                if child.type in ["function_definition", "class_definition"]:
                    # Recurse on functions and classes
                    result.extend(self.__extract_nodes(child, source_code, parent_type=py_mapping[node.type], parent_name=curr_name))
                else:
                    # Non functions and classes only get metadata extracted
                    if node.type not in ["function_definition", "class_definition"]:
                        # Safety check if current node is not a function or class
                        result.append(self.__extract_other_details(child, parent_type=py_mapping[node.type], parent_name=curr_name))
            return result

        # Start processing the current node and add to result
        node_metadata = process_node(node)
        result = []
        curr_name = ""
        if node_metadata is not None:
            curr_name = node_metadata["block_name"]
            result.append(node_metadata)

        # Process child nodes recursively
        result.extend(process_child_nodes(node, curr_name))

        # Sort nodes by start byte offset to ensure correct order
        result.sort(key=lambda x: x.get("start_offset", 0))

        return result

    def __extract_function_details(self, node: Node, parent_name: str, parent_type: str) -> Optional[Dict]:
        """
        Extract function details like name, arguments, return variable, etc.
        """
        node_name = node.child_by_field_name("name")
        if node_name is None:
            return None
        function_name = self.__get_node_text(node_name)

        arguments = self.__extract_function_arguments(node)
        return_variable = self.__extract_return_variable(node)
        functions_called = self.__extract_function_calls(node)
        comments, docstrings = self.__extract_comments_docstrings(node)

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

    def __extract_class_details(self, node: Node, parent_name: str, parent_type: str) -> Optional[Dict]:
        """
        Extract class details including its methods.
        """
        node_name = node.child_by_field_name("name")
        if node_name is None:
            return None
        class_name = self.__get_node_text(node_name)

        methods = self.__extract_class_methods(node, class_name)
        comments, docstrings = self.__extract_comments_docstrings(node)

        return {
            "relative_path": self.file_path,
            "start_offset": node.start_byte,
            "end_offset": node.end_byte,
            "block_type": "class",
            "block_name": class_name,
            "block_args": self.__extract_class_args(methods),
            "parent_type": parent_type,
            "parent_name": parent_name,
            "methods": methods,
            "docstrings": docstrings,
            "comments": comments
        }

    def __extract_other_details(self, node: Node, parent_name: str, parent_type: str) -> Dict:
        """
        Extract metadata for non-class, non-function nodes (e.g., if-statements, loops).
        """
        functions_called = self.__extract_function_calls(node)
        comments, docstrings = self.__extract_comments_docstrings(node)

        return {
            "relative_path": self.file_path,
            "start_offset": node.start_byte,
            "end_offset": node.end_byte,
            "block_type": "others",
            "block_name": f"Block at {node.start_byte}-{node.end_byte}",
            "block_args": [],
            "parent_type": parent_type,
            "parent_name": parent_name,
            "functions_called": functions_called,
            "docstrings": docstrings,
            "comments": comments
        }

    def __get_node_text(self, node: Node) -> str:
        """
        Get text from a node in the AST.
        """
        return self.source_code[node.start_byte: node.end_byte].decode()

    def __extract_function_arguments(self, node: Node) -> List[str]:
        """
        Extract the arguments of a function. Named, unnamed, and typed parameters are supported.
        """
        arguments = []

        query = PY_LANGUAGE.query("""
        (function_definition
          name: (identifier) @function.name
          parameters: (parameters) @function.params
        )
        """)

        captures = query.captures(node)
        arguments = []
        if captures.get("function.params"):
            for capture in captures["function.params"]:
                arguments.extend(self.__extract_params(capture))
        return arguments

    def __extract_params(self, capture) -> List[str]:
        return [param.strip() for param in self.__get_node_text(capture).strip(" ()").split(",")]

    def __extract_return_variable(self, node: Node) -> Optional[str]:
        """
        Extract the return variable from a function.
        """
        return_variable = None
        for child in node.children:
            if child.type == "return_statement":
                return_expr = child.children[0] if child.children else None
                if return_expr and return_expr.type == "identifier":
                    return_variable = self.__get_node_text(return_expr)
        return return_variable

    def __extract_function_calls(self, node: Node) -> List[str]:
        """
        Extract function calls within the node.
        """
        query = PY_LANGUAGE.query("""
            (call) @function_call
        """)
        captures = query.captures(node)
        function_calls = []
        if captures.get("function_call"):
            for capture in captures["function_call"]:
                function_calls.append(self.__get_node_text(capture))
        return function_calls

    def __extract_comments_docstrings(self, node: Node) -> Tuple[List[str], List[str]]:
        """
        Extract comments and docstrings from a node.
        """
        def strip_single_line_comments(text: str) -> str:
            if text.strip().startswith("#"):
                return text.lstrip("#").strip()
            return text

        def strip_docstring(text: str) -> str:
            if text.startswith('"""') and text.endswith('"""'):
                return text[3:-3].strip()
            return text

        query = PY_LANGUAGE.query("""
            (comment) @comment
            (expression_statement (string) @docstring)
        """)
        captures = query.captures(node)

        comments = [strip_single_line_comments(self.__get_node_text(c)) for c in captures.get("comment", [])]
        docstrings = [strip_docstring(self.__get_node_text(c)) for c in captures.get("docstring", [])]
        return comments, docstrings

    def __extract_class_methods(self, node: Node, parent_class_name: str) -> List[Dict]:
        """
        Extract methods within a class.
        """
        methods = []
        node_body = node.child_by_field_name("body")
        if node_body:
            for child in node_body.children:
                if child.type == "function_definition":
                    methods.append(self.__extract_function_details(child, parent_class_name, py_mapping[node.type]))
        return methods

    def __extract_class_args(self, methods: List[Dict]) -> List[str]:
        """
        Extract arguments from the class's methods, assuming from the __init__ method.
        """
        for method in methods:
            if method["block_name"] == "__init__":
                return method["block_args"]
        return []

    def __simplify_metadata(
        self,
        nodes_metadata: List[Dict],
        source_code: bytes,
        text_splitter: Optional[RecursiveCharacterTextSplitter] = None
    ) -> Tuple[List[str], List[Dict]]:
        """
        Simplify metadata by combining "others" nodes (which represent code blocks in global scope) into one document, flattening class methods into their own documents and and using a text splitter on the large "others" block if provided.

        Parts of the code where classes and functions were are replaced with "Code for: <func/class info>"

        The metadata is returned in the order of appearance in the code.

        PS: This class is the messy part of the code since it does metadata formatting.
        """
        if not nodes_metadata:
            return [], []

        all_nodes = []
        others = []
        others_metadata = {
            "relative_path": self.file_path,
            "start_offset": nodes_metadata[0]["start_offset"],
            "end_offset": nodes_metadata[-1]["end_offset"],
            "block_type": "others",
            "block_name": "Combined Others",
            "block_args": [],
            "parent_type": "root",
            "parent_name": "root",
            "functions_called": [],
            "docstrings": [],
            "comments": []
        }
        # Sort nodes by their start offset if not already sorted
        nodes_metadata.sort(key=lambda x: x.get("start_offset", 0))

        # Gather all function/class nodes code blocks as bytes
        all_nodes_text = []

        for node_data in nodes_metadata:
            match node_data["block_type"]:
                case "others":  # Merge code
                    # Append all functions and comments to 'others_metadata'
                    self.__merge_others_metadata(others_metadata, node_data)
                    others.append(source_code[node_data["start_offset"]: node_data["end_offset"]] + b'\n')

                case "function" | "class":
                    # Generate "Code for: " statements using the helper method
                    code_for_str = self.__generate_code_for_block(node_data).encode()
                    others.append(code_for_str)

                    # Handle 'class' blocks, including methods
                    if node_data["block_type"] == "class":
                        node_methods = node_data.get("methods", [])
                        if node_methods:
                            # Set the end point of class as the start point of the first method if any
                            node_data["end_offset"] = node_methods[0]["start_offset"]

                        # Add the class code text
                        node_text = [source_code[node_data["start_offset"]: node_data["end_offset"]]]

                        for node_method in node_methods:
                            # Add methods as their own standalone entries
                            all_nodes.append(node_method)
                            all_nodes_text.append(source_code[node_method["start_offset"]: node_method["end_offset"]])

                            method_code_for_str = self.__generate_code_for_block(node_method).encode()
                            node_text.append(method_code_for_str)
                            others.append(method_code_for_str)

                        all_nodes.append(node_data)
                        all_nodes_text.append(b"".join(node_text).decode())
                    else:
                        all_nodes.append(node_data)

        # Merge all 'others' code blocks into one document
        others_doc = b"".join(others)
        others_doc_text = others_doc.decode()

        # Apply the text splitter if provided
        if text_splitter:
            others_doc_text = self.__apply_text_splitter(others_doc_text, text_splitter)
            others_metadata = [others_metadata for _ in range(len(others_doc_text))]  # Clone metadata for each chunk
        else:
            others_doc_text = [others_doc_text]
            others_metadata = [others_metadata]

        # Combine all nodes
        all_nodes.extend(others_metadata)
        all_nodes_text.extend(others_doc_text)

        # Sort nodes by 'start_offset'
        sorted_nodes = sorted(zip(all_nodes_text, all_nodes), key=lambda x: x[1]["start_offset"])
        all_nodes_text, all_nodes = zip(*sorted_nodes)

        return list(all_nodes_text), list(all_nodes)

    def __merge_others_metadata(self, others_metadata: Dict, node_data: Dict) -> None:
        """
        Append functions_called, docstrings, and comments from the "others" node data into the given metadata.
        """
        for key in ["functions_called", "docstrings", "comments"]:
            others_metadata[key] += node_data.get(key, [])

    def __generate_code_for_block(self, node_data: Dict) -> str:
        """
        Generate "Code for: " statements for blocks of type function/class.
        """
        args = ", ".join(node_data["block_args"])
        return f"# Code for {node_data['block_type']}: {node_data['block_name']}({args})\n"

    def __apply_text_splitter(self, text: str, text_splitter: RecursiveCharacterTextSplitter) -> List[str]:
        """
        Apply the text splitter to the provided text.
        """
        if isinstance(text_splitter, type):
            splitter = text_splitter.from_language(language=langchain_text_splitters.Language.PYTHON,
                                                   chunk_size=256,
                                                   chunk_overlap=16)
        else:
            splitter = text_splitter
        return splitter.split_text(text)

