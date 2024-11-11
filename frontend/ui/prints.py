from typing import Any, Dict, Iterable, List, Optional
import time

def print_stream(response: Iterable[Any]):
    """Print chat completion streaming response in chunks"""
    collected_messages = []
    for chunk in response:
        chunk_message = chunk.choices[0].delta.content
        if chunk_message is not None:
            collected_messages.append(chunk_message)
            print(chunk_message, end="", sep="", flush=True)

    return "".join(collected_messages)


def fake_print_stream(response: str):
    """Makes normal text have a typewriter effect"""
    for word in response.split():
        yield word + " "
        time.sleep(0.05)


