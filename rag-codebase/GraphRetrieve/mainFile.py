from langchain_community.document_loaders import DirectoryLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate, FewShotPromptTemplate
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
import numpy as np
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.vectorstores import Neo4jVector
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
import os
from python_ast import PythonASTDocumentLoader
import re
import neo4j

folderPath = os.getcwd()+"/vectorDB"


embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/multi-qa-mpnet-base-cos-v1",
    model_kwargs={'device': "cuda"})


loader = DirectoryLoader("../../ast_tokenizer",
                         glob="*.py", loader_cls=PythonASTDocumentLoader, recursive=True)

# interpret information in the documents
documents = loader.load()

# augment page data with some meta data
for docs in documents:
    newContent = f"Block Type: {docs.metadata['block_type']} \n Relative Path: {docs.metadata['relative_path'].replace('/',' ')} \n Block Name: {docs.metadata['block_name']} \n Arguments: {' '.join(docs.metadata['block_args'])} \n Code: {' '.join(re.findall('[a-zA-Z0-9]+', docs.page_content))}"
    docs.page_content = newContent


# load the language model - preferably one that is very good at writing code 
llm = OllamaLLM(model="llama3.1:8b",
                num_predict=-1,
                temperature=0.035)

# llm = ChatAnthropic(model="claude-3-sonnet-20240229",
#                     temperature=0,
#                     max_tokens=1024,
#                     timeout=None,
#                     max_retries=2)

# Connect Graph Database 
graph = Neo4jGraph(
    url="bolt://localhost:7687",
    username="neo4j",
    password="testing123",
    enhanced_schema=True,  # Provides more info about available values
)

graph.refresh_schema()
# print(graph.schema)

examples = [
    {
    "question": "How many functions are defined in the file 'example_file.py'?",
    "query": "MATCH (f:Function)-[:IN]->(file:File {{path: 'example_file.py'}}) RETURN count(f)"
    }, 
    {
    "question": "Which functions are called by the function 'calculateTotal'?",
    "query": "MATCH (f:Function {{name: 'calculateTotal'}})-[:CALLS]->(c:Calls) RETURN c.name"
    }, 
    {
    "question": "What are the names of all classes defined in the file 'example_file.py'?",
    "query": "MATCH (c:Class)-[:IN]->(file:File {{path: 'example_file.py'}}) RETURN c.name"
    }, 
    {
    "question": "Which methods belong to the class 'User'?",
    "query": "MATCH (cl:Class {{name: 'User'}})-[:DEFINES]->(m:Method) RETURN m.name"
    }, 
    {
    "question": "What is the file path of the method 'getUserDetails'?",
    "query": "MATCH (m:Method {{name: 'getUserDetails'}})-[:IN]->(file:File) RETURN file.path"
    }, 
    {
    "question": "What functions are called by the methods in 'example_file.py'?",
    "query": "MATCH (m:Method)-[:IN]->(file:File {{path: 'example_file.py'}})-[:CALLS]->(c:Calls) RETURN DISTINCT c.name"
    }, 
    {
    "question": "What comments are associated with the function 'parseData'?",
    "query": "MATCH (f:Function {{name: 'parseData'}}) RETURN f.comments"
    }, 
    {
    "question": "Which methods in the file 'example_file.py' have associated docstrings?",
    "query": "MATCH (m:Method)-[:IN]->(file:File {{path: 'example_file.py'}}) WHERE size(m.docstrings) > 0 RETURN m.name"
    }, 
    {
    "question": "Which classes are defined in 'example_file.py' and have docstrings?",
    "query": "MATCH (c:Class)-[:IN]->(file:File {{path: 'example_file.py'}}) WHERE size(c.docstrings) > 0 RETURN c.name"
    }, 
    {
    "question": "Which files contain both classes and methods?",
    "query": "MATCH (f:File)-[:IN]->(c:Class), (f)-[:IN]->(m:Method) RETURN DISTINCT f.path"
    }
]


example_prompt = PromptTemplate.from_template("User input: {question}\nCypher query: {query}")

# Smarter way to pick closest examples to the query
# example_selector = SemanticSimilarityExampleSelector.from_examples(
#     examples,
#     embeddings,
#     Neo4jVector,
#     k=5,
#     input_keys=["question"],
# )

# prompt = FewShotPromptTemplate(
#     examples=examples_selector,
#     example_prompt=example_prompt,
#     prefix="You are a Neo4j expert. Given an input question, create a syntactically correct Cypher query to run.\n\nHere is the schema information\n{schema}.\n\nBelow are a number of examples of questions and their corresponding Cypher queries.",
#     suffix="User input: {question}\nCypher query: ",
#     input_variables=["question", "schema"],
# )

# print(example_selector.select_examples({"question": "How many files are there?"}))

# print(example_prompt.invoke(example_selector.select_examples({"question": "How many files are there?"})[0]))

# TODO: Change its goal to attempt to return the files that are most relevant instead so further processing can be done
prompt = FewShotPromptTemplate(
    examples=examples[:],
    example_prompt=example_prompt,
    prefix="You are a Neo4j expert. Given an input question, create a syntactically correct Cypher query to run.\n\nHere is the schema information\n{schema}.\n\nBelow are a number of examples of questions and their corresponding Cypher queries. Take note of the schema before answering, it should be one of the valid types with the valid relationships that you retrieve with.",
    suffix="User input: {question}\nCypher query: ",  # leave the query to generate open-ended for LLM to fill
    input_variables=["question", "schema"],
)

#prefix="You are a Neo4j expert. Given an input question, create a syntactically correct Cypher query to run.\n\nHere is the schema information\n{schema}.\n\nHere are the list of files\n {files}\n\nBelow are a number of examples of questions and their corresponding Cypher queries. Take note of the schema before answering, it should be one of the valid types with the valid relationships that you retrieve with.",

graph_chain = GraphCypherQAChain.from_llm(
    graph=graph, 
    llm=llm, 
    cypher_prompt=prompt, 
    verbose=True, 
    allow_dangerous_requests=True, 
    validate_cypher=True,
    # use_function_response=True  # From testing so far, the LLM needs more context on what is in the graph db - This is broken as of the newest langchain
)
# print(graph_chain.invoke("How many files are in the graph?"))

# prompt = PromptTemplate(template="""
# Context: {context}
# 
# You are a Python codebase analyzer. Use the provided repository context to answer questions. Reply the answer and with a code snippet if possible.
# If you do now know the answer or are unable to generate the cypher given the schema, just say you do not have enough information.
# Cite specific files,function names, and locations in your answers. For example: "(Function: create_new_token, Path: home/User/repo/func.py)".
# 
# At the end of your commentary, if you gave a good answer: 
# 1. Create a list of citations used with (Path, function name)
# 2. Suggest a further question that can be answered by the paragraphs provided. 
# 
# 
# Question: {input} 
# 
# Answer:""",
#                         input_variables=['input', 'context'])
# 

while True:
    prompt = input("What do you want to ask?\n").lower()
    try:
        response = graph_chain.invoke(prompt)
        print(response)
    except neo4j.exceptions.CypherSyntaxError:
        print("Invalid Cypher was generated")
