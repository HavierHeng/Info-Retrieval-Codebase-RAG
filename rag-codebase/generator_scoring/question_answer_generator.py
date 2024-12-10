from langchain_community.document_loaders import DirectoryLoader
from langchain_core.documents import Document
from langchain_core.runnables.base import Runnable
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from typing import List
import re
import random
import tqdm
import argparse
from python_ast import PythonASTDocumentLoader
import json
import os

def docPreprocessing(documents):
    """
    To match the preprocessing done in the RAG pipeline
    """
    for docs in documents:
        newContent = f"Block Type: {docs.metadata['block_type']} \n Relative Path: {docs.metadata['relative_path'].replace('/',' ')} \n Block Name: {docs.metadata['block_name']} \n Arguments: {' '.join(docs.metadata['block_args'])} \n Code: {' '.join(re.findall('[a-zA-Z0-9]+', docs.page_content))}"
        docs.page_content = newContent

# def customSplitter(listOfDocuments, token_len=2, overlap=1):
#     """
#     To match the splitting and cleaning done in the RAG
#     """
#     listOfToken = []
#     for document in listOfDocuments:
#         pagecontent = document.page_content.lower()
#         pagecontent = document.page_content.replace("_", " ")
#         listToAdd = []
#         for x in range(overlap, len(pagecontent), token_len):
#             end_index = min(x+token_len, len(pagecontent))
#             listToAdd.append(pagecontent[x-overlap:end_index])
#         listOfToken.append(listToAdd)
#     return listOfToken


def generate_question_answer_pair(llm_chain: Runnable, docs: List[Document], pair_count: int, reference_docs_count:int) -> str:
    """
    Given a list of documents, randomly pick out some references and use that to generate a question and its list of references.

    llm_chain is a Langchain Runnable, such as a Chain or LLM.

    docs is a set of Documents that you want to use as the input text.

    pair_count is the number of question-answer pairs that is desired to be generated.

    reference_docs_count is the number of reference docs that the LLM will randomly try to sample from the document list. Note that reference docs can have extremely varying contexts. This is alright as this is meant to be used as a subset of the full document corpus.


    Returns as a JSON string.
    """
    outputs = []

    for _ in tqdm.trange(pair_count, desc="Question-Answer Pair"):
        sampled_context = random.sample(docs, reference_docs_count)
        # Generate QA couple
        output_QA_couple = llm_chain.invoke(input={"context": sampled_context})
        try:
            question = output_QA_couple.split("Factoid question: ")[-1].split("Answer: ")[0]
            answer = output_QA_couple.split("Answer: ")[-1]
            assert len(answer) < 300, "Answer is too long"
            outputs.append(
                {
                    "context": [content.page_content for content in sampled_context],
                    "question": question,
                    "answer": answer,
                    "reference_file": [content.metadata["relative_path"] for content in sampled_context]
                }
            )
        except:
            continue
    return json.dumps(outputs, indent=4)


def parse_args():
    parser = argparse.ArgumentParser(description="Generate Question-Answer pairs in a target directory/repo")

    parser.add_argument(
        "repo_path",
        type=str,
        help="Path to the repository (absolute or relative)"
    )

    parser.add_argument(
        "--preprocess",
        action="store_true",
        help="Whether to do custom preprocessing on the data (default is False)"
    )

    parser.add_argument(
        "--pair-count",
        type=int,
        default=10,
        help="Number of question-answer pairs to generate (default is 10)"
    )

    parser.add_argument(
        "--ref-docs-count",
        type=int,
        default=3,
        help="Number of reference documents to use as a context to generate the question and answer pair (default is 3)"
    )

    parser.add_argument(
        '--save-to', 
        type=str, 
        default=None,  # If not provided, output is printed to stdout
        help="Path to save the output to a file. If not specified, prints to stdout."
    )

    args = parser.parse_args()

    # Ensure the repository path is valid
    if not os.path.exists(args.repo_path):
        raise ValueError(f"The provided repository path '{args.repo_path}' does not exist.")

    # Additional validation (optional): check if counts are positive
    if args.pair_count <= 0:
        raise ValueError("The pair count must be a positive integer.")
    if args.ref_docs_count <= 0:
        raise ValueError("The reference docs count must be a positive integer.")
    return args
            

def main():
    args = parse_args()
    loader = DirectoryLoader(args.repo_path,
                             glob="*.py", loader_cls=PythonASTDocumentLoader, recursive=True)
    documents = loader.load()
    if args.preprocess:
        docPreprocessing(documents)

    # load the language model
    llm = OllamaLLM(model="llama3.1:8b",
                    num_predict=-1,
                    temperature=0.035)

    qa_generation_prompt = PromptTemplate(template=""" 
    Your task is to write a factoid question and an answer given a context.
    The question should be something a developer might naturally ask when analyzing or working with this code. For example:
      - What does this function do?
      - What will this return for input `foobar`?
      - How does this behave when the input is negative?
      - How do I deserialize json data?
      - How do I start up a flask app server?
      - How do I configure routes? 
      - How do I create a custom error handler? 
      - Are there ways to implement test cases for this part of my application? 
      - Does flask handle password hashing? 
      - Does flask have ORM features?
      - Can you render frontend with flask?
  
    The question should not refer to the code as "this code" or "context", but rather focus on the actual behavior of the code.
    Keep the question natural, as if you were explaining the code to someone else in a casual setting, and it must be formulated in the same style as questions users could ask in a search engine or a forum.
    Provide your answer in a clear, technical manner, focused on the code’s functionality or expected behavior.

    Your factoid question should be answerable with a specific, concise piece of factual information from the context.

    Provide your answer as follows:

    Output:::
    Factoid question: (your factoid question)
    Answer: (your answer to the factoid question)

    Now here is the context.

    Context: {context}\n
    Output:::""", input_variables=['context'])


    qa_chain = create_stuff_documents_chain(llm, qa_generation_prompt)

    result = generate_question_answer_pair(qa_chain, documents, args.pair_count, args.ref_docs_count)

     # If --save-to is specified, save the result to that file
    if args.save_to:
        with open(args.save_to, 'w') as file:
            file.write(result)
        print(f"Output saved to {args.save_to}")
    else:
        # Otherwise, print to stdout
        print(result)
    
if __name__ == "__main__":
    main()
