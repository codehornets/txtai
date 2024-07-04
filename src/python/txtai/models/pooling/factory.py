"""
Factory module
"""

import json
import os

from huggingface_hub import hf_hub_download
from huggingface_hub.utils import EntryNotFoundError

from .base import Pooling
from .cls import ClsPooling
from .mean import MeanPooling


class PoolingFactory:
    """
    Method to create pooling models.
    """

    @staticmethod
    def create(config):
        """
        Create a pooling model.

        Args:
            config: pooling configuration

        Returns:
            Pooling
        """

        # Unpack parameters
        method, path, device, tokenizer, maxlength, modelargs = [
            config.get(x) for x in ["method", "path", "device", "tokenizer", "maxlength", "modelargs"]
        ]

        # Derive maxlength, if applicable
        maxlength = PoolingFactory.maxlength(path) if isinstance(maxlength, bool) and maxlength else maxlength

        # Default pooling returns hidden state
        if isinstance(path, bytes) or (isinstance(path, str) and os.path.isfile(path)) or method == "pooling":
            return Pooling(path, device, tokenizer, maxlength, modelargs)

        # Derive pooling method if it's not specified, path is a string and path is not a local path
        if (not method or method not in ("clspooling", "meanpooling")) and (isinstance(path, str) and not os.path.exists(path)):
            method = PoolingFactory.method(path)

        # Check for cls pooling
        if method == "clspooling":
            return ClsPooling(path, device, tokenizer, maxlength, modelargs)

        # Default to mean pooling
        return MeanPooling(path, device, tokenizer, maxlength, modelargs)

    @staticmethod
    def method(path):
        """
        Determines the pooling method using the sentence transformers pooling config.

        Args:
            path: model path

        Returns:
            pooling method
        """

        # Default method
        method = "meanpooling"

        try:
            # Load 1_Pooling/config.json file
            config = PoolingFactory.load(path, "1_Pooling/config.json")

            # Set to CLS pooling if it's enabled and mean pooling is disabled
            if config["pooling_mode_cls_token"] and not config["pooling_mode_mean_tokens"]:
                method = "clspooling"

        # Ignore this error
        except EntryNotFoundError:
            pass

        return method

    @staticmethod
    def maxlength(path):
        """
        Reads the max_seq_length parameter from sentence transformers config.

        Args:
            path: model path

        Returns:
            max sequence length
        """

        # Default length is unset
        maxlength = None

        # Read max_seq_length from sentence_bert_config.json
        try:
            config = PoolingFactory.load(path, "sentence_bert_config.json")
            maxlength = config.get("max_seq_length")

        # Ignore this error
        except EntryNotFoundError:
            pass

        return maxlength

    @staticmethod
    def load(path, name):
        """
        Loads a JSON config file from the Hugging Face Hub.

        Args:
            path: model path
            name: file to load

        Returns:
            config
        """

        # Download file and parse JSON
        path = hf_hub_download(repo_id=path, filename=name)
        with open(path, encoding="utf-8") as f:
            return json.load(f)
