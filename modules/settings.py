# -*- coding: utf-8 -*-

"""
Here I store the universal settings (external paths, etc) for the project.
"""
from tools.util.settings import Settings

__author__ = "Jakrin Juangbhanich"
__email__ = "juangbhanich.k@gmail.com"


class ProjectSettings(Settings):

    _INSTANCE = None

    @staticmethod
    def instance() -> 'ProjectSettings':
        """ Singleton Access. """
        if ProjectSettings._INSTANCE is None:
            ProjectSettings("settings.yaml")
        return ProjectSettings._INSTANCE

    def __init__(self, path: str):
        super().__init__()

        ProjectSettings._INSTANCE = self

        self.LABELS_FILE = "NONE"
        self.GROUND_TRUTH_FILE = "NONE"
        self.IMAGE_URL_FILE = "NONE"

        self.OUTPUT_DIRECTORY = "NONE"
        self.SAMPLES_DIRECTORY = "NONE"
        self.STORAGE_DIRECTORY = "NONE"

        self.load(path)
