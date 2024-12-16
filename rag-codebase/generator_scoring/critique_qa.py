# Metrics taken from: https://huggingface.co/papers/2312.10003
from langchain_community.document_loaders import DirectoryLoader
from langchain_core.documents import Document
from langchain_core.runnables.base import Runnable
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from tqdm import tqdm
import pandas as pd
import argparse
import os
import json


question_groundedness_critique_prompt = """
You will be given a context and a question.
Your task is to provide a 'total rating' scoring how well one can answer the given question unambiguously with the given context.
Give your answer on a scale of 1 to 5, where 1 means that the question is not answerable at all given the context, and 5 means that the question is clearly and unambiguously answerable with the context.

Provide your answer as follows:

Answer:::
Evaluation: (your rationale for the rating)
Total rating: (your rating)

Now here are the question and context.

Question: {question}\n
Context: {context}\n
Answer::: """

question_relevance_critique_prompt = """
You will be given a question.
Your task is to provide a 'total rating' representing how useful this question can be when assisting Python developers to understanding and program using a complex or foreign codebase.
Give your answer on a scale of 1 to 5, where 1 means that the question is not useful at all, and 5 means that the question is extremely useful.

Provide your answer as follows:

Answer:::
Evaluation: (your rationale for the rating)
Total rating: (your rating)

Now here is the question.

Question: {question}\n
Answer::: """

question_standalone_critique_prompt = """
You will be given a question.
Your task is to provide a 'total rating' representing how context-independant this question is.
Give your answer on a scale of 1 to 5, where 1 means that the question only makes sense in a specific context, and 5 means that the question makes sense by itself.
For instance, if the question refers to a particular setting, like 'in the context' or 'in the document', the rating must be 1.
The questions can contain obscure technical nouns or acronyms like Gradio, Hub, Hugging Face or Space and still be a 5: it must simply be clear to an operator with access to documentation what the question is about.

Provide your answer as follows:

Answer:::
Evaluation: (your rationale for the rating)
Total rating: (your rating)

Now here is the question.

Question: {question}\n
Answer::: """

llm = ChatOllama(model="llama3.1:8b",
                num_predict=-1,
                temperature=0.035)

question_groundedness_critique_prompt = ChatPromptTemplate.from_template(
    question_groundedness_critique_prompt
)

question_groundedness_critique_agent = question_groundedness_critique_prompt | llm

question_relevance_critique_prompt = ChatPromptTemplate.from_template(
    question_relevance_critique_prompt
)
question_relevance_critique_agent = question_relevance_critique_prompt | llm

question_standalone_critique_prompt = ChatPromptTemplate.from_template(
    question_standalone_critique_prompt
)
question_standalone_critique_agent = question_standalone_critique_prompt | llm

def critique_qa_pairs(qa_pairs):
    print("Generating critique for each QA couple...")
    for qa_pair in tqdm(qa_pairs):
        # Critique the generated QA couple
        question_groundedness_evaluation = question_groundedness_critique_agent.invoke(
            {"context": qa_pair["context"], "question": qa_pair["question"]}
        ).content
        question_relevance_evaluation = question_relevance_critique_agent.invoke(
            {"question": qa_pair["question"]}
        ).content
        question_standalone_evaluation = question_standalone_critique_agent.invoke(
            {"question": qa_pair["question"]}
        ).content

        try:
            groundedness_score = int(question_groundedness_evaluation.split("Total rating: ")[1][0])
            groundedness_eval = question_groundedness_evaluation.split("Total rating: ")[0].split(
                "Evaluation: "
            )[1]
            relevance_score = int(question_relevance_evaluation.split("Total rating: ")[1][0])
            relevance_eval = question_relevance_evaluation.split("Total rating: ")[0].split(
                "Evaluation: "
            )[1]
            standalone_score = int(question_standalone_evaluation.split("Total rating: ")[1][0])
            standalone_eval = question_standalone_evaluation.split("Total rating: ")[0].split(
                "Evaluation: "
            )[1]
            qa_pair.update(
                {
                    "groundedness_score": groundedness_score,
                    "groundedness_eval": groundedness_eval,
                    "relevance_score": relevance_score,
                    "relevance_eval": relevance_eval,
                    "standalone_score": standalone_score,
                    "standalone_eval": standalone_eval,
                }
            )
        except:
            continue

def filter_low_scores(scored_qa_pairs):
    generated_questions = pd.DataFrame.from_dict(scored_qa_pairs)
    print(len(generated_questions))
    generated_questions = generated_questions.loc[
        (generated_questions["groundedness_score"] >= 4)
        & (generated_questions["relevance_score"] >= 4)
        & (generated_questions["standalone_score"] >= 4)
    ]
    return generated_questions.to_dict("records")


def parse_args():
    parser = argparse.ArgumentParser(description="Filter Question-Answer pairs based on their groundedness, relevance and standalone scores")

    parser.add_argument(
        "file_path",
        type=str,
        help="Path to the qa pair json file"
    )

    parser.add_argument(
        '--save-to', 
        type=str, 
        default=None,  # If not provided, output is printed to stdout
        help="Path to save the output to a file. If not specified, prints to stdout."
    )

    args = parser.parse_args()

    # Ensure the file path is valid
    if not os.path.exists(args.file_path):
        raise ValueError(f"The file path '{args.file_path}' does not exist.")
    return args


def main():
    args = parse_args()

    with open(args.file_path, "r") as file:
        data = json.load(file)

    print("Loaded", len(data), "QA Pairs")
    critique_qa_pairs(data)
    result = filter_low_scores(data)
    print("Final Number of QA Pairs:", len(result))

     # If --save-to is specified, save the result to that file
    if args.save_to:
        with open(args.save_to, 'w') as file:
            file.write(json.dumps(result, indent=4))
        print(f"Output saved to {args.save_to}")
    else:
        # Otherwise, print to stdout
        print(result)

if __name__ == "__main__":
    main()
