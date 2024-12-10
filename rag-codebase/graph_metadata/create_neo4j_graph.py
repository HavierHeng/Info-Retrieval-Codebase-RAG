from neo4j import GraphDatabase
import argparse
import os
from langchain_community.document_loaders import DirectoryLoader
from tqdm import tqdm
import argparse
from python_ast import PythonASTDocumentLoader
import os

# Functions include both class methods and functions
FUNCTION_QUERY = """
    // Create the File node if it doesn't exist
    MERGE (file:File {path: $relative_path})

    // Create the Function node if it doesn't exist
    MERGE (function:Function {name: $block_name, relative_path: $relative_path})
        ON CREATE SET function.start_offset = $start_offset, function.end_offset = $end_offset, function.comments = $comments, function.docstrings = $docstrings, function.functions_called = $functions_called

    // Link Function to its parent (either a Class or Others block)
    MERGE (parent:Node {name: $parent_name, relative_path: $relative_path})
    MERGE (parent)-[:CONTAINS]->(function)

    // Create CALLS relationships for functions the current function calls
    WITH function, parent, $functions_called AS functions_called
    UNWIND functions_called AS called_function
    MERGE (called_func:Function {name: called_function})
    MERGE (function)-[:CALLS]->(called_func)

    RETURN function, parent, file
    """

# Class contain references to methods
CLASS_QUERY = """
    // Create the File node if it doesn't exist
    MERGE (file:File {path: $relative_path})

    // Create the Class node if it doesn't exist
    MERGE (class:Class {name: $block_name, relative_path: $relative_path})
        ON CREATE SET class.start_offset = $start_offset, class.end_offset = $end_offset, class.comments = $comments, class.docstrings = $docstrings

    // Create relationship from File to Class block
    MERGE (file)-[:CONTAINS]->(class)

    // Create methods and link them to the class
    WITH class, file, $methods AS methods
    UNWIND methods AS method_data
    MERGE (method:Method {name: method_data.block_name, parent_class: $block_name, relative_path: $relative_path})
        ON CREATE SET method.start_offset = method_data.start_offset, method.end_offset = method_data.end_offset, method.comments = method_data.comments, method.docstrings = method_data.docstrings, method.functions_called = method_data.functions_called

    // Create relationship between Class and Method (DEFINES)
    MERGE (class)-[:DEFINES]->(method)

    RETURN class, file, method
    """

# Others are code that live in the global scope
OTHERS_QUERY = """
    // Create the File node if it doesn't exist
    MERGE (file:File {path: $relative_path})

    // Create an "Others" node for global scope or non-class content
    MERGE (others:Others {name: $block_name, relative_path: $relative_path})
        ON CREATE SET others.start_offset = $start_offset, others.end_offset = $end_offset, others.comments = $comments, others.docstrings = $docstrings, others.functions_called = $functions_called

    // Create relationship from File to Others block
    MERGE (file)-[:CONTAINS]->(others)

    RETURN others, file
    """

# Function to import a JSON object into Neo4j
def import_metadata(tx, metadata):
    """
    tx represents a Neo4j transaction.
    metadata is the metadata from the Custom ASTDocumentLoader Document.

    The nodes created are:
    - File
    - Class
    - Function
    - Others 

    The nodes each have their own properties based on the metadata:
    - Class
        {
            "relative_path": <str>,
            "start_offset": <int>,
            "end_offset": <int>,
            "block_type": "class",
            "block_name": <str>,
            "block_args": [],
            "parent_type": <str>,j
            "parent_name": <str>,
            "methods": <Dict[Dict]>,
            "docstrings": [],
            "comments": [] 
        }

    - Function
        {
            "relative_path": <str>,
            "start_offset": <int>,
            "end_offset": <int>,
            "block_type": "function",
            "block_name": <str>,
            "block_args": [],
            "parent_type": <str>,
            "parent_name": <str>,
            "return_var_ast": <str>,
            "functions_called": [],
            "docstrings": [],
            "comments": [] 
        }

    - Others
         {
            "relative_path": <str>,
            "start_offset": <int>,
            "end_offset": <int>,
            "block_type": "others",
            "block_name": "Global Scope",
            "block_args": [],
            "parent_type": "root",
            "parent_name": "root",
            "functions_called": [],
            "docstrings": [],
            "comments": []
        }


    """
    if metadata["block_type"] == "function":
        query = FUNCTION_QUERY
    elif metadata["block_type"] == "class": 
        query = CLASS_QUERY
    elif metadata["block_type"] == "others":
        query = OTHERS_QUERY
    else:
        print("Unknown block type")
        return

    tx.run(query, **metadata)


def parse_args():
    parser = argparse.ArgumentParser(description="Load documents from a directory")
    parser.add_argument("directory", type=str, help="The directory containing files to parse")
    parser.add_argument("username", type=str, help="Neo4J database username", default="neo4j")
    parser.add_argument("password", type=str, help="Neo4J database password", default="neo4j")
    parser.add_argument("database", type=str, help="Neo4J database", default="testing")
    
    args = parser.parse_args()

    # Ensure the repository path is valid
    if not os.path.exists(args.directory):
        raise ValueError(f"The provided repository path '{args.directory}' does not exist.")
    return args

def main():
    args = parse_args()
    loader = DirectoryLoader(args.directory, glob=f"*.py", loader_cls=PythonASTDocumentLoader)

    try:
        documents = loader.load()
        print(f"Loaded {len(documents)} documents from {args.directory})")
    except Exception as e:
        print(f"Error: {e}")
        raise e

    # Initialize Neo4j driver
    uri = "bolt://localhost:7687"
    driver = GraphDatabase.driver(uri, auth=(args.username, args.password))

    with driver.session(database=args.database) as session:
        for document in tqdm(documents, desc="Graphing Documents..."):
            session.execute_write(import_metadata, document.metadata)

if __name__ == "__main__":
    main()
