from langchain_text_splitters import (
    Language,
    RecursiveCharacterTextSplitter,
)
from langchain_community.document_loaders import DirectoryLoader, PythonLoader
from langchain_community.document_loaders.parsers.language.python import PythonSegmenter

with open("../../frontend/ui/ui.py") as f:
    PYTHON_CODE = f.read()

python_splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.PYTHON, chunk_size=50, chunk_overlap=0
)
python_docs = python_splitter.create_documents([PYTHON_CODE])

# for doc in python_docs:
# Splitter splits per line or statement naively
# print(type(doc), doc)


print("\n\n\n")
print("TESTINGTESTINGTESTING")
print("\n\n\n")

loader = PythonLoader("mainFile.py")
loader_docs = loader.load()

# for doc in loader_docs:
# PythonLoader has a large chunk size, but can load from files directly
# Results in one huge document, that needs further recursive splitting
# print(type(doc), doc)

segmenter = PythonSegmenter(PYTHON_CODE)
print(segmenter.is_valid())
print("\n Class Func\n")
print(segmenter.extract_functions_classes())
print("\n Simplified \n")
print(segmenter.simplify_code())
