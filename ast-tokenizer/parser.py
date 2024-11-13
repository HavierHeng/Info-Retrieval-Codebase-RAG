import tree_sitter_python as tspython
from tree_sitter import Language, Parser
import glob
import os
import argparse
# import gitpython
import languages


# TODO: GITPYTHON - for pulling files
# TODO: ARGPARSE - for cloning then parsing
# TODO: GLOB FOR ONLY PYTHON FILES
# TODO: FILE.READ() instead of bytes
# TODO: PARALLELIZED TREE SITTING WTH
# TODO: IMPROVE TOKENIZER - SUPPORT FOR READING ALL TOP LEVEL CLASSES AND FUNCTIONS, AS WELL AS ALL DOCSTRINGS


# https://tree-sitter.github.io/py-tree-sitter/classes/tree_sitter.Tree.html

def main():
    PY_LANGUAGE = Language(tspython.language())

    parser = Parser(PY_LANGUAGE)
   
    tree_bytes = parser.parse(read_callable_byte_offset, encoding="utf8")
    tree_point = parser.parse(read_callable_point, encoding="utf8")
    # walk_tree(tree_bytes, src)
    tokenize_blocks_from_root(tree_bytes, src)

if __name__ == "__main__":
    main()
