#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Draw the labels on a couple of samples.
"""

import argparse
import os
import cv2
from modules.loader import Loader
from modules.settings import ProjectSettings
from tools.util.logger import Logger

__author__ = "Jakrin Juangbhanich"
__email__ = "juangbhanich.k@gmail.com"


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--set_index", default=0, type=int, help="The index of the set to use.")
    parser.add_argument("-n", "--sample_count", default=50, type=int, help="How many do we want to visualize?")
    return parser.parse_args()


args = get_args()
set_index = args.set_index
sample_count = args.sample_count

if __name__ == "__main__":

    # Load the project settings and required modules.
    Logger.log_special("Running Sample Loader", with_gap=True)
    settings = ProjectSettings("settings.yaml")

    # Load the label mapping.
    loader = Loader()
    loader.load_labels(settings.LABELS_FILE)
    Logger.log_field("Labels Loaded", len(loader.label_map))

    # Load the samples from the set that we want.
    samples = Loader.load_sample_set(set_index)
    loaded_samples = [s for s in samples if (s.is_locally_loaded and len(s.detect_regions) > 0)]

    # How many samples loaded?
    n_loaded_samples = len(loaded_samples)
    Logger.log_field("Samples with Images", n_loaded_samples)
    if n_loaded_samples == 0:
        raise Exception("None of the samples in this set have been downloaded! "
                        "Please run cmd_load_sample_images first for this set.")
    loaded_samples = loaded_samples[:min(n_loaded_samples - 1, sample_count)]

    # Create the output folder for this part.
    set_path = os.path.join(settings.OUTPUT_DIRECTORY, "gt_visualization", f"set_{set_index}")
    os.makedirs(set_path, exist_ok=True)

    for sample in loaded_samples:

        image = sample.get_visualized_image(label_map_function=loader.get_label)
        file_name = os.path.join(set_path, f"{sample.key}.jpg")
        cv2.imwrite(file_name, image)
