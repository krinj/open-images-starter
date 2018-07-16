#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Once the sample sets have been created via cmd_create_samples, you can use this
script to download the individual sample images from the remote URL.
"""

import argparse
import os
import threading
import time
from modules.loader import Loader
from modules.settings import ProjectSettings
from tools.util.logger import Logger

__author__ = "Jakrin Juangbhanich"
__email__ = "juangbhanich.k@gmail.com"


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--set_index", default=0, type=int, help="The index of the set to use.")
    parser.add_argument("-m", "--max_threads", default=5, type=int, help="Max threads to use for loading.")
    return parser.parse_args()


args = get_args()
set_index = args.set_index
max_threads = args.max_threads


if __name__ == "__main__":

    # Load the project settings and required modules.
    Logger.log_special("Running Sample Loader", with_gap=True)
    settings = ProjectSettings("settings.yaml")

    set_path = os.path.join(settings.SAMPLES_DIRECTORY, f"sample_set_{set_index}.json")
    if not os.path.exists(set_path):
        Logger.log_field("Error", "No file found at {}. Have you created the samples using cmd_create_samples yet?")
        exit(1)

    Logger.log_special("Begin Sample Image Download", with_gap=True)
    samples = Loader.load_sample_set_from_file(set_path)
    unloaded_samples = [s for s in samples if not s.is_locally_loaded]
    n_unloaded_samples = len(unloaded_samples)
    n_samples = len(samples)
    Logger.log_field("Samples Loaded", "{}/{}".format(n_samples - n_unloaded_samples, n_samples))

    i = 0

    for sample in unloaded_samples:
        while True:
            if threading.active_count() <= max_threads:
                thread = threading.Thread(target=sample.load)
                thread.start()
                break
            else:
                time.sleep(1)

        i += 1
        Logger.log_field("Loading Sample", f"{i}/{n_unloaded_samples}")
