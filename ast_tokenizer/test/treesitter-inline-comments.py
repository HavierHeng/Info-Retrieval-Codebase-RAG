from tree_sitter import Language, Parser
import tree_sitter_python as tspython

# Load the language (e.g., Python)
PYLANGUAGE = Language(tspython.language())
parser = Parser(PYLANGUAGE)

def extract_comments(source_code):
    # Parse the source code into a syntax tree
    tree = parser.parse(bytes(source_code, 'utf-8'))

    # Define a query to capture both line and block comments
    query = PYLANGUAGE.query("""
        (comment) @comment
        (expression_statement (string) @comment)
    """)

    # Run the query on the tree
    captures = query.captures(tree.root_node)

    comments = []
    for node in captures["comment"]:
        comment_text = source_code[node.start_byte:node.end_byte].encode('utf-8')
        comments.append(comment_text)

    return comments

# Example usage
source_code = """
# This is a single-line comment
def foo():
    '''This is a block comment'''
    pass  # Another inline comment
import random
import asyncio
def read_file(file_name):
    with open(file_name, 'r') as f:
        return f.read()

# Write some text to a file
with open('sample.txt', 'w') as f:
    f.write("Hello, world!\nThis is a test file.")

# Call the function to read and print the file contents
read_file('sample.txt')

def invis():
    return

# Create a simple list and calculate the sum
numbers = [1, 2, 3, 4, 5]
total = sum(numbers)
print(f"Sum of numbers: {total}")

def test_print(who, two, three, *args, **kwargs):
    print(who)

class Person:
    ''' 
    Defines a person - Docstring
    ''' 
    SURPRISE = "SURPRISE"
    def __init__(self, name):
        # Init - standalone comment
        self.name = name

    def intro(self):
        print("I am", self.name)  # Greet someone - Inline comment

    def curse(self, target):

        def random_curse(self):
            return random.choice(["idiot", "dumbass", "fool"])

        return "".join([target, "you", random_curse()])

async def count():
    print("One")
    await asyncio.sleep(1)
    print("Two")

tomas = Person("tomathy")
"""

comments = extract_comments(source_code)
for comment in comments:
    print(comment)

