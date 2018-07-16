# -*- coding: utf-8 -*-

"""
Abstract class for importing YAML file settings into a Python format.
"""

import json
import os
import shutil

import yaml
from .logger import Logger

__author__ = "Jakrin Juangbhanich"
__email__ = "juangbhanich.k@gmail.com"


class Settings:

    def __init__(self):
        pass

    def load(self, path: str):

        """ Look for the matching attributes in the .env and set them here. """

        # Copy the example file if the real file doesn't exist yet.
        if not os.path.exists(path):
            example_path = path.replace(".", "-example.")
            Logger.log("{} does not exist. Will copy the sample from {}.".format(path, example_path))
            shutil.copy2(example_path, path)

        # Read YAML file.
        with open(path, 'r') as stream:
            data = yaml.load(stream)

        Logger.log_special("Load {}".format(self.__class__.__name__), with_gap=True)

        for attribute in self.__dict__:
            if not hasattr(self, attribute):
                continue

            if attribute not in data:
                Logger.log_field_red("{} (Default)".format(attribute), getattr(self, attribute))
                continue

            env_val = data[attribute]
            attr_type = type(getattr(self, attribute))

            if attr_type is int:
                setattr(self, attribute, int(env_val))

            elif attr_type is float:
                setattr(self, attribute, float(env_val))

            elif attr_type is bool:
                setting_value = env_val == "True"
                setattr(self, attribute, setting_value)

            elif attr_type.__name__ == "NoneType":
                setattr(self, attribute, env_val)

            elif attr_type is list:
                setattr(self, attribute, json.loads(env_val))

            elif attr_type is str:
                setattr(self, attribute, env_val)

            else:
                raise Exception(
                    "Could not set attribute on settings object, the attribute {} has an unsupported type {}"
                    .format(attribute, attr_type.__name__))

            Logger.log_field(attribute, getattr(self, attribute))

