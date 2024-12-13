from langchain_community.document_loaders import DirectoryLoader
from python_ast import PythonASTDocumentLoader
loader = DirectoryLoader("/home/yuesheng/flask",
                         glob="*.py", loader_cls=PythonASTDocumentLoader, recursive=True)
documents = loader.load()

with open("document_reference.txt", "w") as f:
    for x in documents:
        f.write("____________________________________________________________________________________________________\n")
        f.write(f"Name: {x.metadata['block_name']}\n")
        f.write(f"Type: {x.metadata['block_type']}\n")
        f.write(f"Parent Type: {x.metadata['parent_name']}\n")
        f.write(
            f"Location: {x.metadata['relative_path']},{x.metadata['start_offset']},{x.metadata['end_offset']}\n")
        f.write(f"Arguments: {x.metadata['block_args']}\n")
        f.write(f"Code: {x.page_content}\n")
        f.write("____________________________________________________________________________________________________\n")
