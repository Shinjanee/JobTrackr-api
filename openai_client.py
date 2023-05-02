import random
import logging
import openai
from flask import Flask, jsonify, request
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY_LIST = [os.getenv("API_KEY")]

class GPTClient:
    def __init__(self):
        self.parameters = {
            "model": "gpt-3.5-turbo",
            "presence_penalty": 1.2,
            "frequency_penalty": 1.2,
            "temperature": 0.7,
        }
        self.api_key_list = API_KEY_LIST
        self.ALLOWED_PARAMETERS = {
            "model": str,
            "temperature": float,
            "top_p": float,
            "max_tokens": int,
            "presence_penalty": float,
            "frequency_penalty": float,
            "logit_bias": dict,
            "user": str,
        }

        # Configure logger
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def customize_model_parameters(self, customizations):
        disallowed_keys = set(customizations) - set(self.ALLOWED_PARAMETERS)
        if disallowed_keys:
            raise ValueError(f"Parameters {disallowed_keys} are not allowed.")

        for key, value in customizations.items():
            t = self.ALLOWED_PARAMETERS[key]
            if not isinstance(value, t):
                raise ValueError(
                    f"Value {value} for parameter {key} is of invalid type {type(value)}. "
                    f"Allowed type is {self.ALLOWED_PARAMETERS[key]}."
                )
        self.parameters.update(customizations)

    def generate_reply(self, messages, retries=3):
        self.logger.info(f"\nPrompt: {messages}")
        openai.api_key = random.choice(self.api_key_list)
        exception_list = []
        for retry in range(retries):
            try:
                self.logger.info(f"Waiting on OpenAI...")
                response = openai.ChatCompletion.create(
                    **self.parameters, messages=messages
                )
                self.logger.info(f"OpenAI responded!")
                return (
                    response["choices"][0]["message"]["content"],
                    response["usage"]["total_tokens"],
                )
            except Exception as e:
                exception_list.append(e)

        error_string = ""
        for retry_index, exception in enumerate(exception_list):
            error_string += f"Retry {retry_index + 1}: {repr(exception)}\n"
        raise ValueError(error_string)


gpt_client = GPTClient()
