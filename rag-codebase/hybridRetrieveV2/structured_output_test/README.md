# Structured Output

Using Pydantic to force output is not possible with small models from Ollama. They hallucinate so often the output doesn't fit the strict output defined by Pydantic. Paid models like OpenAI and Anthropic works fine though. But then it won't be a fair comparison.

For most langchain stuff that needs function calling, this is a common pattern.

Thought it would be really nice to have structured output just cos its easier to evaluate docs this way.
