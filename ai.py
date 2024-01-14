import json
import logging
import config
import openai
import backoff
from typing import List

# Set up logging
logger = logging.getLogger(__name__)


def fsystem(msg):
    return {"role": "system", "content": msg}


def fuser(msg):
    return {"role": "user", "content": msg}


def fassistant(msg):
    return {"role": "assistant", "content": msg}


class AI:
    def __init__(self, api_key, model_name="gpt-4-0314", temperature=0.1, endpoint_base_url=None):
        """
        Initialize the AI class.

        Parameters
        ----------
        api_key : str
            The API key for authentication.
        model_name : str, optional
            The name of the model to use, by default "gpt-4-1106-preview".
        temperature : float, optional
            The temperature to use for the model, by default 0.1.
        endpoint_base_url : str, optional
            The base URL for the API, by default None.
        """
        self.temperature = temperature
        self.model_name = model_name
        if endpoint_base_url:
            self.client = openai.OpenAI(api_key=api_key, base_url=endpoint_base_url)
        else:
            self.client = openai.OpenAI(api_key=api_key)

    def get_embedding(self, texts: list[str] | str, model="text-embedding-ada-002"):
        if isinstance(texts, str):
            texts = texts.replace("\n", " ")
            return self.client.embeddings.create(input=[texts], model=model).data[0].embedding
        texts = [t.replace("\n", " ") for t in texts]
        embeddings = self.client.embeddings.create(input = texts, model=model)
        return [e.embedding for e in embeddings.data]

    @backoff.on_exception(backoff.expo, openai.RateLimitError, max_tries=7, max_time=45)
    def chat_completion(self, messages: list[dict], max_tokens: int | None = None, **kwargs) -> str:
        """
        Generate a response using the language model with backoff.

        Parameters
        ----------
        messages : list[dict]
            The conversation history.
        max_tokens : int
            The maximum number of tokens to generate.

        Returns
        -------
        str
            The content of the response message.
        """
        # Use temperature from kwargs if provided
        if "temperature" in kwargs:
            temperature = kwargs["temperature"]
        else:
            temperature = self.temperature

        if max_tokens:
            response = self.client.chat.completions.create(
                messages=messages,
                model=self.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                # **kwargs
            )
        else:
            response = self.client.chat.completions.create(
                messages=messages,
                model=self.model_name,
                temperature=temperature,
                # **kwargs
            )
        logger.info(f"Chat completion response: {response}")
        return response.choices[-1].message.content


def serialize_messages(messages: List[dict]) -> str:
    """
    Serialize a list of messages to a JSON string.

    Parameters
    ----------
    messages : List[dict]
        The list of messages to serialize.

    Returns
    -------
    str
        The serialized messages as a JSON string.
    """
    return json.dumps(messages)


gpt4_ai = AI(api_key=config.OPENAI_API_KEY, model_name="gpt-4-0314")
mixtral_ai = AI(api_key=config.TOGETHER_API_KEY,
                model_name="mistralai/Mixtral-8x7B-Instruct-v0.1",
                endpoint_base_url="https://api.together.xyz")
# response = ai_instance.chat_completion([fsystem("Hello"), fuser("How are you?")], max_tokens=100)