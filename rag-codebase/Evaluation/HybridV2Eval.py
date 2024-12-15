from ragas import evaluate
from ragas.metrics import LLMContextRecall, Faithfulness, FactualCorrectness, ResponseRelevancy
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_anthropic import ChatAnthropic
from ragas.llms import LangchainLLMWrapper
from dataset import data_samples_V1
from datasets import Dataset
import os
from dotenv import load_dotenv

load_dotenv()

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/multi-qa-mpnet-base-cos-v1",
    model_kwargs={'device': "cuda"})

evaluator_llm = LangchainLLMWrapper(ChatAnthropic(model="claude-3-haiku-20240307", temperature=0))
metrics = [LLMContextRecall(), FactualCorrectness(), Faithfulness(), ResponseRelevancy()]
results = evaluate(dataset=Dataset.from_dict(data_samples_V1), metrics=metrics, llm=evaluator_llm, embeddings=embeddings)
results.to_pandas() 

print(results)