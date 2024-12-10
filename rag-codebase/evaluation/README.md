# Evaluation of models and hyperparams
## Datasets

CodeQA

CodeXGLUE
- Code-Code
- Code-Text

Custom - any code base (but we trying on Flask dataset)
- Works by just random.choice documents and generating question answer pairs using another model.
- Negative tests can be tested by mixing up some of the question and references

## Tools
BLEU/BLEURT
- The reference data is cleaned up removing all special characters and text, as both of these methods rely on n-grams to calculate how well the output references text

DeepEval

