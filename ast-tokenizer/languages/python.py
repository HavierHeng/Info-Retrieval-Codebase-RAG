# Source for python treesitter types: https://github.com/tree-sitter/tree-sitter-python/tree/master
mapping = {
        "function": "function_definition",
        "class": "class_definition",
        "method": "method_definition",
        "type_def": "type_alias_declaration"
    }
src = bytes(
        """
def foo():
    if bar:
        baz()

def read_callable_byte_offset(byte_offset, point):
    return src[byte_offset : byte_offset + 1]


def read_callable_point(byte_offset, point):
    row, column = point
    if row >= len(src_lines) or column >= len(src_lines[row]):
        return None
    return src_lines[row][column:].encode("utf8")

# https://tree-sitter.github.io/py-tree-sitter/classes/tree_sitter.Tree.html


class Dumbass:
    def __init__(self, dumb):
        self.dumb = dumb
    def yapper(self):
        print("REEEEEEEEEEEEEEE")


if __name__ == "__main__":
    main()
""",
        "utf8"
    )

### TYPES I SAW
# function_definition
# class_definition
# if_statement
# comment
 
src_lines = ["\n", "def foo():\n", "    if bar:\n", "        baz()\n"]

def read_callable_byte_offset(byte_offset, point):
    return src[byte_offset : byte_offset + 1]


def read_callable_point(byte_offset, point):
    row, column = point
    if row >= len(src_lines) or column >= len(src_lines[row]):
        return None
    return src_lines[row][column:].encode("utf8")


def tokenize_blocks_from_root(tree, original):
    cursor = tree.walk()
    cursor.goto_first_child()
    counter = 1

    # Print the first block
    print(f"\n ---------- BLOCK {counter} ---------- \n", original[cursor.node.start_byte: cursor.node.end_byte])
    print_func_class_names(cursor, original)  
    counter += 1

    while cursor.goto_next_sibling():  # Continue until there are no more siblings
        print(f"\n  ----------  BLOCK {counter} ---------- \n", original[cursor.node.start_byte: cursor.node.end_byte])
        print_func_class_names(cursor, original)
        counter += 1

def print_func_class_names(cursor, original):
    # Given a cursor which is the direct child of a root node
    # Step into each direct child
    old_pos = cursor.copy()  # unfortunately copying it too many times causes a seg fault - so we have to just do it one by one
    if cursor.node.type == "function_definition" or cursor.node.type == "class_definition":
        cursor.goto_first_child()  # `def` or `class` keyword
        cursor.goto_next_sibling()  # name of function or class
        print("NAME: ", original[cursor.node.start_byte:cursor.node.end_byte])
    cursor.reset_to(old_pos)  # Shift cursor back

def walk_tree(tree, original):
    cursor = tree.walk()

    assert cursor.node.type == "module"

    assert cursor.goto_first_child()
    assert cursor.node.type == "function_definition"  # foo()

    result = cursor.goto_next_sibling()
    while result:
        result = cursor.goto_next_sibling()  # jump to __name__=="__main__"
    print(original[cursor.node.start_byte: cursor.node.end_byte])

    cursor.goto_first_child()
    cursor.goto_first_child()

    # assert cursor.node.type == "def"

    # Returns `False` because the `def` node has no children
    # assert not cursor.goto_first_child()

    cursor.goto_next_sibling()
    # assert cursor.node.type == "identifier"
    print(cursor.node.start_byte, cursor.node.end_byte, cursor.node.text, original[cursor.node.start_byte: cursor.node.end_byte])

    cursor.goto_next_sibling()
    # assert cursor.node.type == "parameters"

    cursor.goto_parent()
    # assert cursor.node.type == "function_definition"
    # What i want to get is
    # 1) Byte offset of interesting bits - esp its name
    # 2) 


    # Testing so far
    # Okay so interesting shits are
    # Taking nodes children seem to move down the list
    # From root node/module -> Sibling == going to next block
    # From root node -> Child -> Child == first function def
    

    # What are all the datastructure
    # Tree
    # Node
    # TreeCursor
    # Point - idk


