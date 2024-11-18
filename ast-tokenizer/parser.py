import argparse
import os
from langchain_community.document_loaders import PythonLoader, JavascriptLoader

LANGUAGE_LOADERS  = {
        "py": PythonLoader,  # Default Loader - Reads Python files as is, without splitting
        "js": JavascriptLoader,
        # "py-ast": 
        # "js-ast":
}

def load_documents(directory, file_type):
    """
    Load documents based on file type. 
    """
    if file_type not in LANGUAGE_LOADERS:
        raise ValueError(f"Unsupported file type: {file_type}. Supported types: {', '.join(LANGUAGE_LOADERS.keys())}")

    # Get the correct loader class based on file extension
    loader_class = LANGUAGE_LOADERS[file_type]
    loader = loader_class()  # Instantiate the loader
    
    # Load the documents from all matching files in the directory
    documents = []
    for filename in os.listdir(directory):
        if filename.endswith(f".{file_type}"):
            file_path = os.path.join(directory, filename)
            documents.extend(loader.load(file_path))  # Adjust as per the actual loader's method
    return documents

def main():
    # Setup argument parsing
    parser = argparse.ArgumentParser(description="Load documents from a directory")
    parser.add_argument('directory', type=str, help="The directory containing files to parse")
    parser.add_argument('file_type', choices=LANGUAGE_LOADERS.keys(), help="The language of code files")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Load documents based on input
    try:
        documents = load_documents(args.directory, args.file_type)
        print(f"Loaded {len(documents)} documents from {args.directory} (file type: {args.file_type})")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

