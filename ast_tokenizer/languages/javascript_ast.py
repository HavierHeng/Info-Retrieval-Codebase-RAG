# https://github.com/tree-sitter/tree-sitter-javascript/blob/master/grammar.js
import tree_sitter_javascript as tsjavascript
from tree_sitter import Language, Node, Parser
from typing import Iterator, Union, Optional, List, Dict, Tuple
from pathlib import Path
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import langchain_text_splitters

JS_LANGUAGE = Language(tsjavascript.language())
JS_PARSER = Parser(JS_LANGUAGE)

JS_MAPPING = {
    "function_declaration": "function",
    "arrow_function": "function",
    "function_expression": "function",
    "class_declaration": "class",
    "program": "root",  # JS AST root is typically a "program"
    "method_definition": "method",
    "variable_declaration": "variable",
    "expression_statement": "expression"
}

class JavascriptASTDocumentLoader(BaseLoader):
    """
    Javascript DocumentLoader that uses Treesitter to parse its abstract syntax trees, 
    and return Document objects that contain blocks (defined by functions, classes, or other structures).
    """

    def __init__(self, file_path: Union[str, Path]):
        self.file_path = file_path

    def lazy_load(self) -> Iterator[Document]:
        with open(self.file_path, "rb") as f:
            code_file_bytes = f.read()
            self.source_code = code_file_bytes
            tree = JS_PARSER.parse(code_file_bytes)
            
            self.current_position = 0
            
            all_nodes_metadata = self.__extract_nodes(tree.root_node, code_file_bytes, "root", "")
            
            all_nodes_text, all_nodes_metadata = self.__simplify_metadata(all_nodes_metadata, code_file_bytes)
            
            for node_text, node_metadata in zip(all_nodes_text, all_nodes_metadata):
                yield Document(page_content=node_text, metadata=node_metadata)

    def __should_process_node(self, node: Node) -> bool:
        """
        Determine if a node should be processed as a block.
        This is so that nodes that are not blocks - i.e in global scope are skipped instead of processed unnecessarily.

        This also deals with the special case where variable declaration contains functions - cos thanks javascript.
        """
        if node.type not in JS_MAPPING:
            return False
            
        if node.type in ["function_declaration", "function_expression", "arrow_function", "class_declaration", "class_expression", "method_definition"]:
            return True
            
        # Check for variable declarations that contain functions
        if node.type == "variable_declaration":
            for child in node.children:
                if child.type == "variable_declarator":
                    value = child.child_by_field_name("value")
                    if value and value.type in ["arrow_function", "function_expression"]:
                        return True
        return False

    def __extract_nodes(self, node: Node, source_code: bytes, parent_type: str = "root", parent_name: str = "") -> List[Dict]:
        """
        Extract nodes recursively from the AST and return a list of node metadata using DFS strategy.

        Functions and classes are recursed, while others blocks are processed as is. Parent name (derived from recursion) and type (derived from the node) are based on the current nodes name and type.
        """
        result = []

        # If current node is within the processable blocks - then try to process it
        if self.__should_process_node(node):
            node_metadata = self.__process_node(node, parent_name, parent_type)
            if node_metadata:
                self.current_position = node.end_byte
                result.append(node_metadata)

        # Process children - via DFS recursion
        for child in node.children:
            result.extend(self.__extract_nodes(child, source_code, JS_MAPPING.get(node.type, "root"), parent_name))
            
        return result

    def __process_node(self, node: Node, parent_name: str, parent_type: str) -> Optional[Dict]:
         """Process a node based on its type and return metadata."""
         if node.type in ["function_declaration", "function_expression"]:
             return self.__extract_function_details(node, parent_name, parent_type)
         elif node.type == "arrow_function":
             return self.__extract_arrow_details(node, parent_name, parent_type)
         elif node.type in ["class_declaration", "class_expression"]:
             return self.__extract_class_details(node, parent_name, parent_type)
         elif node.type == "method_definition":
             return self.__extract_method_details(node, parent_name, parent_type)
         elif node.type == "variable_declaration":
             # Handle variable declarations containing functions
             for child in node.children:
                 if child.type == "variable_declarator":
                     value = child.child_by_field_name("value")
                     if value and value.type in ["arrow_function", "function_expression"]:
                         return self.__extract_function_details(value, parent_name, parent_type)
         return None

    def __extract_function_details(self, node: Node, parent_name: str, parent_type: str) -> Optional[Dict]:
        """
        Extract function details like name, arguments, return variable, etc.
        In Javascript, function_expression and method_definition is used by class methods, while function_declaration is used by function.

        Handles both function declarations and expressions.
        """

        # Handle different ways of getting function name based on declaration type
        name_node = node.child_by_field_name("name")
        if name_node:  # If there is a name, since js can have anon functions
            function_name = self.__get_node_text(name_node)
        else:
            # Try to get name from parent variable declaration - for anon func
            parent = node.parent
            if parent and parent.type == "variable_declarator":
                name_node = parent.child_by_field_name("name")
                if name_node:
                    function_name = self.__get_node_text(name_node)
                # Orphaned anon function
                else:
                    function_name = "anonymous"
            else:
                function_name = "anonymous"
            
        arguments = self.__extract_function_arguments(node)
        return_variable = self.__extract_return_variable(node)
        functions_called = self.__extract_function_calls(node)
        comments = self.__extract_comments(node)

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
            "comments": comments
        }

    def __extract_arrow_details(self, node: Node, parent_name: str, parent_type: str) -> Optional[Dict]:
        """
        Extract details from arrow functions.
        """
        # Try to get name from parent variable declaration
        parent = node.parent
        function_name = "anonymous"
        if parent and parent.type == "variable_declarator":
            name_node = parent.child_by_field_name("name")
            if name_node:
                function_name = self.__get_node_text(name_node)

        arguments = self.__extract_arrow_arguments(node)
        return_variable = self.__extract_return_variable(node)
        functions_called = self.__extract_function_calls(node)
        comments = self.__extract_comments(node)

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
            "comments": comments
        }

    def __extract_method_details(self, node: Node, parent_name: str, parent_type: str) -> Optional[Dict]:
        """
        Extract details from class methods.
        """
        node_name = node.child_by_field_name("name")
        if node_name is None:
            return None
            
        method_name = self.__get_node_text(node_name)
        arguments = self.__extract_function_arguments(node)
        return_variable = self.__extract_return_variable(node)
        functions_called = self.__extract_function_calls(node)
        comments = self.__extract_comments(node)

        return {
            "relative_path": self.file_path,
            "start_offset": node.start_byte,
            "end_offset": node.end_byte,
            "block_type": "method",
            "block_name": method_name,
            "block_args": arguments,
            "parent_type": parent_type,
            "parent_name": parent_name,
            "return_var_ast": return_variable,
            "functions_called": functions_called,
            "comments": comments
        }

    def __extract_function_arguments(self, node: Node) -> List[str]:
        """
        Extract function arguments, supporting both regular and arrow functions.
        """
        params_node = node.child_by_field_name("parameters")
        if not params_node:
            return []

        arguments = []
        for param in params_node.children:
            if param.type == "identifier":
                arguments.append(self.__get_node_text(param))
            elif param.type == "formal_parameters":
                # Handle destructured parameters
                arguments.extend(self.__extract_destructured_params(param))

        return arguments

    def __extract_arrow_arguments(self, node: Node) -> List[str]:
        """
        Extract arguments specifically from arrow functions.
        """
        params_node = node.child_by_field_name("parameters")
        if not params_node:
            # Handle single parameter without parentheses
            param = node.child_by_field_name("parameter")
            if param and param.type == "identifier":
                return [self.__get_node_text(param)]
            return []

        return self.__extract_function_arguments(node)

    def __extract_destructured_params(self, node: Node) -> List[str]:
        """
        Extract parameters from destructuring patterns.
        """
        params = []
        for child in node.children:
            if child.type == "identifier":
                params.append(self.__get_node_text(child))
            elif child.type in ["object_pattern", "array_pattern"]:
                # Handle nested destructuring
                params.append(f"{{{self.__get_node_text(child)}}}")
        return params

    def __extract_class_details(self, node: Node, parent_name: str, parent_type: str) -> Optional[Dict]:
        """
        Extract class details including its methods.
        """
        node_name = node.child_by_field_name("name")
        if node_name is None:
            return None
            
        class_name = self.__get_node_text(node_name)
        body_node = node.child_by_field_name("body")
        
        methods = []
        if body_node:
            for child in body_node.children:
                if child.type == "method_definition":
                    method_data = self.__extract_method_details(child, class_name, "class")
                    if method_data:
                        methods.append(method_data)

        comments = self.__extract_comments(node)
        
        return {
            "relative_path": self.file_path,
            "start_offset": node.start_byte,
            "end_offset": node.end_byte,
            "block_type": "class",
            "block_name": class_name,
            "block_args": self.__extract_constructor_args(methods),
            "parent_type": parent_type,
            "parent_name": parent_name,
            "methods": methods,
            "comments": comments
        }

    def __extract_constructor_args(self, methods: List[Dict]) -> List[str]:
        """
        Extract arguments from the class's constructor method.
        """
        for method in methods:
            if method["block_name"] == "constructor":
                return method["block_args"]
        return []    

    def __get_node_text(self, node: Node) -> str:
        """
        Get text from a node in the AST.
        """
        return self.source_code[node.start_byte: node.end_byte].decode()


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
        query = JS_LANGUAGE.query("""
            (call_expression) @function_call
        """)
        captures = query.captures(node)
        function_calls = []
        if captures.get("function_call"):
            for capture in captures["function_call"]:
                function_calls.append(self.__get_node_text(capture))
        return function_calls

    def __extract_comments(self, node: Node) -> List[str]:
        """
        Extract all comments from a node.
        Javascript has two types of comments - single lines and multilines
        """
        # Define a query to match comments
        query_string = """
        (comment) @comment
        """
        query = JS_LANGUAGE.query(query_string)
        
        # Get all comments within the node's range
        captures = query.captures(node)
        comments = []
        if captures.get("comment"): 
            for capture in captures["comment"]:
                comment_text = self.__get_node_text(capture)
                # Clean up the comment text
                if comment_text.startswith('//'):
                    comment_text = comment_text[2:].strip()
                elif comment_text.startswith('/*') and comment_text.endswith('*/'):
                    comment_text = comment_text[2:-2].strip()
                
                if comment_text:
                    comments.append(comment_text)
        
        return comments

    def __simplify_metadata(
        self,
        nodes_metadata: List[Dict],
        source_code: bytes,
        text_splitter: Optional[RecursiveCharacterTextSplitter] = None
    ) -> Tuple[List[str], List[Dict]]:
        """
        Simplify metadata by combining "others" nodes (which represent code blocks in global scope) into one document, flattening class methods into their own documents and and using a text splitter on the large "others" block if provided.

        Code blocks if containing some other block have a stand in "// Code for ..." format:
        - Classes: "// Code for class: name(params)"
        - Methods: "// Code for method: class.method(params)"
        - Functions: "// Code for function: name(params)"

        The metadata is returned in the order of appearance in the code.

        PS: This class is the messy part of the code since it does metadata formatting.
        """

        if not nodes_metadata:
            return [], []

        all_nodes = []
        all_nodes_text = []
        
        # Create a list of all block ranges to identify "others" content
        block_ranges = []
        for node in nodes_metadata:
            block_ranges.append((node["start_offset"], node["end_offset"]))
        
        # Sort ranges to make it easier to iterate
        block_ranges.sort()

        # Process blocks (functions, classes, methods)
        for node_data in nodes_metadata:
            if node_data["block_type"] == "class":
                # For classes, we want to replace method implementations with summaries
                class_text = source_code[node_data["start_offset"]:node_data["end_offset"]].decode()
                methods = node_data.get("methods", [])
                
                # Replace each method implementation with a summary line
                for method in methods:
                    method_text = source_code[method["start_offset"]:method["end_offset"]].decode()
                    method_summary = f"// Code for {method['block_type']}: {method['parent_name']}.{method['block_name']}({', '.join(method['block_args'])})\n"
                    class_text = class_text.replace(method_text, method_summary)
                
                all_nodes.append(node_data)
                all_nodes_text.append(class_text)
                
                # Add methods as separate documents
                for method in methods:
                    method_text = source_code[method["start_offset"]:method["end_offset"]].decode()
                    all_nodes.append(method)
                    all_nodes_text.append(method_text)
            else:
                # Handle regular functions and other blocks
                node_text = source_code[node_data["start_offset"]:node_data["end_offset"]].decode()
                all_nodes.append(node_data)
                all_nodes_text.append(node_text)

        # Sort nodes by start_offset to maintain original code order
        sorted_nodes = sorted(zip(all_nodes_text, all_nodes), key=lambda x: x[1]["start_offset"])
        all_nodes_text, all_nodes = zip(*sorted_nodes)

        return list(all_nodes_text), list(all_nodes)

    def __process_global_scope(
        self,
        others_text: str,
        others_metadata: Dict,
        text_splitter: Optional[RecursiveCharacterTextSplitter] = None
    ) -> Tuple[List[str], List[Dict]]:
        """
        Apply the text splitter to the provided text.
        Adds a comment to identify which block this code belongs from
        """
        processed_texts = []
        processed_metadata = []
        
        # Add "Code for" prefix for Global Scope
        global_scope_code = "// Code for Global Scope\n" + others_text

        # Apply text splitter if provided
        if text_splitter:
            # Initialize the splitter based on whether it's a class or instance
            if isinstance(text_splitter, type):
                splitter = text_splitter.from_language(language=langchain_text_splitters.Language.JS)
            else:
                splitter = text_splitter
                
            # Split the text and process chunks
            others_chunks = splitter.split_text(global_scope_code)
            for i, chunk in enumerate(others_chunks, 1):
                # For split chunks, add chunk number to distinguish them
                chunk_prefix = f"// Code for Global Scope (Part {i})\n"
                if not chunk.startswith("// Code for"):  # Avoid double prefix
                    chunk = chunk_prefix + chunk
                processed_metadata.append(others_metadata.copy())
                processed_texts.append(chunk)
        else:
            processed_metadata.append(others_metadata)
            processed_texts.append(global_scope_code)
            
        return processed_texts, processed_metadata
