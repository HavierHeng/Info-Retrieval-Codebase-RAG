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
The key idea of using an AST for preprocessing
The goal of using a smarter processing system that is code aware and able to pick out different blocks of code, maintaing the overall structure of the code.

AST provides several benefits
1) Mostly language agnostic 
2) Removes unnecessary tokens like braces, semicolons and parenthesis


## Setup

## Pre-Requisites 

You should have Python 3 installed before using this tokenizer. Verify this with either:
- `python --version`
- `python3 --version`

The project is set up in a virtualenv (`venv`)
1) Activate the virtualenv: 
    - Windows: `ast-tokenizer/bin/activate` or `ast-tokenizer/bin/activate.ps1` if in powershell
    - Linux/MacOS (based on shell): `source ast-tokenizer/bin/activate.sh`
2) Check that environment is activated - terminal prompt should show something like
```
(ast-tokenizer) $
```
3) Install dependencies - `pip install -r requirements.txt`

## Execution

The tokenizer can be run in two modes:
1) As a library - this is for integration into other parts of the project flow - such as Langchain
2) As a CLI tool - for parsing individual files
    - Command: `python parser.py` will print the options available 

## TODOs/Missing features

The current implementation mainly picks up top level classes and functions in each file. This might miss out some code from the source database.

## Acknowledgements

### Treesitter - AST parsing and defintions
[Tree Sitter](https://github.com/tree-sitter/tree-sitter) which allows the processing of a language independent abstract syntax tree.

### Language Parsers
[Tree Sitter Python](https://github.com/tree-sitter/tree-sitter-python) for Python 2/3 parsing
[Tree Sitter Javascript](https://github.com/tree-sitter/tree-sitter-javascript) for Javascript/ECMAscript parsing
[Tree Sitter Typescript](https://github.com/tree-sitter/tree-sitter-typescript/blob/master/common/define-grammar.js) for Typescript parsing

[Tree Sitter Go](https://github.com/tree-sitter/tree-sitter-go) for Golang parsing
[Tree Sitter Java](https://github.com/tree-sitter/tree-sitter-java) for Java parsing
