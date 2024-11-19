# AST Tokenizer

## Description

This is a custom tokenizer for languages supported by the RAG system. The tokenizer currently aims to support mainly Python and Javascript, and will parse the functions source code files into metadata in JSON format that can be further processed and indexing into a RAG database.

### What is an AST?
An [Abstract Syntax Tree](https://en.wikipedia.org/wiki/Abstract_syntax_tree) (AST) a data structure used in computer science to represent the structure of a program or code snippet. It is a tree representation of the abstract syntactic structure of text (often source code) written in a formal language. Each node of the tree denotes a construct occurring in the text. 

While parse trees mainly capture the syntatic structure of source code, an abstract syntax tree adds extra semantic information to the tree. This provides more information for each "node" which can be used to extract relevant information, e.g code block position and indexing. It also removes most inessential and language specific punctuations e.g braces, semicolons, parenthesis.

These can be played with on [AST Explorer](https://astexplorer.net/).

### What is Treesitter?
[Tree-sitter](https://tree-sitter.github.io/tree-sitter/) is a parser generator tool and an incremental parsing library. It can build a concrete syntax tree for a source file and efficiently update the syntax tree as the source file is edited. 

Tree-sitter aims to be:
- General enough to parse any programming language
- Fast enough to parse on every keystroke in a text editor
- Robust enough to provide useful results even in the presence of syntax errors
- Dependency-free so that the runtime library (which is written in pure C) can be embedded in any application

For the tokenizer, it is used to easily support multiple languages without needing to rewrite or hook into language specific parsers - e.g for Python it would use Python's [ast](https://docs.python.org/3/library/ast.html) while for golang it would need Go's [ast](https://pkg.go.dev/go/ast). Supporting so many languages without an intermediary library would be tedious:
1) Need to rewrite a parser for each language in its own language
2) Recreate a language neutral AST format for each language and port it to each language parser

The Python bindings for tree-sitter is used in this tokenizer. While there are still language specific patterns, statements and constructs - these can be largely handled by making a custom mapping for these constructs via dictionary to common language constructs.

## Reasoning behind design 

### Why use an AST?
The hypothesis was to tokenize the input source code into metadata that sufficiently represents the codebase, by picking key class, function, argument, return values and docstrings that explain what the code is doing. This reduces the token cost when sending to an LLM, but also makes the retrieval process aware of the syntax of the code - since code is organized by blocks rather than nearby lines.

The is makes for a smarter processing system that is code-aware and able to pick out different blocks of code, maintaing the overall structure and relation of the code.

AST provides several benefits:
1) Mostly language agnostic representation - making it easy to turn into a document to be indexed
2) Removes unnecessary tokens like braces, semicolons and parenthesis
3) Syntatic knowledge - Code cannot be tokenized like a normal text document in that relations are encapsulated by code blocks (e.g think of a class or function block), rather than only considering nearby lines
4) Information on where the original code is located - allowing for references to be made for a RAG system


The output of the AST should aim to create individual source code blocks which represent a document to be indexed into the RAG pipeline.
- e.g: a class named `Foo` is a document
- e.g 2: a function named `Bar` is a document 

## What currently exists in Langchain? And why still making own implementation - Novelty of solution

In Langchain the following methods exist (the examples are for Python Language parsers):
1) [LangChain Community - Python Document Loader](https://api.python.langchain.com/en/latest/document_loaders/langchain_community.document_loaders.python.PythonLoader.html)
    - +: Parses into Langchain Document objects
    - -: Just a file opener, based on their source code.
    - -: Huge chunk sizes, require further text splitting to make sense of code.
2) [LangChain - Recursive Character Text Splitter](https://python.langchain.com/docs/how_to/code_splitter/)
    - +: Parses into Langchain Document objects
    - -: Naive, splits by separators, so it can accidentally remove context, e.g for a class with many methods and a small chunk overlap, documents page_content can end up not including the class they belong to.
    - -: No extra classification of code features. Only understands the raw syntax of code, without understanding its potential relations.
3) [LangChain Community - Python Segmenter](https://api.python.langchain.com/en/latest/_modules/langchain_community/document_loaders/parsers/language/python.html#PythonSegmenter.simplify_code)
    - +: Closest to what we need, uses AST to pick out function and class definitions via `extract_functions_classes()`. Also keeps statements not in class/function blocks via `simplify_code()`. (Was implenting this before discovering it exists)
    - -: Does not create Langchain Document objects. This means that it fails to add metadata like file location, offsets where the source came from, type of code block and important details like important return values and so on. 
4) [LangChain Community - Generic Loader](https://python.langchain.com/api_reference/community/document_loaders/langchain_community.document_loaders.generic.GenericLoader.html)
    - +: Closest to what is needed, uses AST to pick out function and class defintions. Also does the same `simplify_code()` formatting as Segmenter.
    - +: Creates Langchain Document objects.
    - +: Has pretty good support out of the box for most languages.
    - -: Metadata is lacking. It doesn't add enough data to generate citations, and lazily combines functions and classes together.

These solutions are close but not enough. Python Segmenter and Generic Loader is super close, yet falls short as it splits for text, without attaching enough metadata for other uses.

A custom DocumentLoader based on Treesitter and PythonSegmenter's design that returns Langchain `Document` files is made. This serves as an experimentation platform for how much metadata is needed for retrieval.

## Setup

## Pre-Requisites 

You should have Python 3 installed before using this tokenizer. Verify this with either:
- `python --version`
- `python3 --version`

The project is set up in a virtualenv (`venv`)
1) Create venv: `python -m venv .venv`
2) Activate the virtualenv: 
    - Windows: `.venv/bin/activate` or `ast-tokenizer/bin/activate.ps1` if in powershell
    - Linux/MacOS (based on shell): `source .venv/bin/activate.sh`
3) Check that environment is activated - terminal prompt should show something like
```
(.venv) $
```
3) Install dependencies - `pip install -r requirements.txt`

## Execution

The tokenizer can be run in two modes:
1) As a Langchain document loader - this is for integration into other parts of the project flow
2) As a CLI tool - for parsing individual files
    - Command: `python parser.py` will print the options available 

## TODOs
- [ ] Package as a library
- [ ] LLM metadata using local llm function calling

## Acknowledgements

### Treesitter - AST parsing and defintions
[Tree Sitter](https://github.com/tree-sitter/tree-sitter) which allows the processing of a language independent abstract syntax tree.

### Language Parsers
[Tree Sitter Python](https://github.com/tree-sitter/tree-sitter-python) for Python 2/3 parsing

[Tree Sitter Javascript](https://github.com/tree-sitter/tree-sitter-javascript) for Javascript/ECMAscript parsing

[Tree Sitter Typescript](https://github.com/tree-sitter/tree-sitter-typescript/blob/master/common/define-grammar.js) for Typescript parsing


### LangChain 
[Article: How to create a custom Document Loader](https://python.langchain.com/docs/how_to/document_loader_custom/)
