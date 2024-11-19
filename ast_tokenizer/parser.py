import argparse
from langchain_community.document_loaders import PythonLoader, DirectoryLoader
from languages.python_ast import PythonASTDocumentLoader
from languages.javascript_ast import JavascriptASTDocumentLoader
from pprint import pprint
import warnings
warnings.filterwarnings("ignore")
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from functools import partial

LANGUAGE_LOADERS = {
    "py": [
        {"name": "Python Loader", "loader": PythonLoader},
        {"name": "Generic Python Loader", "loader": partial(GenericLoader.from_filesystem, glob="*", suffixes=[".py"], parser=LanguageParser())},
        {"name": "(Custom) Python AST Document Loader", "loader": PythonASTDocumentLoader}
    ],
    "js": [
        {"name": "Generic JS Loader", "loader": partial(GenericLoader.from_filesystem, glob="*", suffixes=[".js"], parser=LanguageParser())},
        {"name": "(Custom) Javascript AST Document Loader", "loader": JavascriptASTDocumentLoader} 
    ]
}

def load_documents(directory, file_type, loader_choice):
    """
    Load documents based on file type and user-selected loader.
    """
    if file_type not in LANGUAGE_LOADERS:
        raise ValueError(f"Unsupported file type: {file_type}. Supported types: {', '.join(LANGUAGE_LOADERS.keys())}")

    # Get the list of loaders for the specified file type
    loaders = LANGUAGE_LOADERS[file_type]
    
    # Ensure that the loader choice is within the available options
    if loader_choice < 0 or loader_choice >= len(loaders):
        raise ValueError(f"Invalid loader choice. Please choose a number between 0 and {len(loaders) - 1}.")
    
    # Get the selected loader class
    selected_loader_class = loaders[loader_choice]["loader"]

    # Set up the DirectoryLoader with the selected loader
    loader = DirectoryLoader(directory, glob=f"*.{file_type}", loader_cls=selected_loader_class)
    
    # Load the documents
    documents = loader.load()
    return documents

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Load documents from a directory")
    parser.add_argument('directory', type=str, help="The directory containing files to parse")
    parser.add_argument('file_type', choices=LANGUAGE_LOADERS.keys(), help="The language of code files")
    
    # Parse arguments
    args = parser.parse_args()

    # List the available loaders for the selected file type
    available_loaders = LANGUAGE_LOADERS[args.file_type]
    print(f"Available loaders for {args.file_type} files:")
    
    for idx, loader_info in enumerate(available_loaders):
        print(f"{idx}. {loader_info['name']}")  # Display the human-readable name

    # Ask the user to choose a loader
    loader_choice = int(input("Please select a loader by number: "))
    
    # Load documents using the selected loader
    try:
        documents = load_documents(args.directory, args.file_type, loader_choice)
        print(f"Loaded {len(documents)} documents from {args.directory} (file type: {args.file_type})")
        for i, document in enumerate(documents, 1):
            if document.metadata.get("block_type") == "others":
                print(f"---------Doc Meta {i}----------")
                pprint(document.metadata)
                print(f"*---------Page Content {i}----------*")
                print(document.page_content)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
