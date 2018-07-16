#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Run some basic statistical analysis on the samples.
"""

import os
from typing import Dict

from modules.loader import Loader
from modules.settings import ProjectSettings
from tools.util.logger import Logger
import matplotlib.pyplot as plt
import numpy as np

__author__ = "Jakrin Juangbhanich"
__email__ = "juangbhanich.k@gmail.com"


def display_stats(instances: Dict[str, int],
                  title: str="SOMETHING",
                  file_name: str="graph_name",
                  n_display: int = 20):

    sorted_instances = sorted(instances.items(), key=lambda kv: kv[1])
    sorted_instances.reverse()

    Logger.log_special(title, with_gap=True)
    for i in range(n_display):
        Logger.log_field(loader.get_label(sorted_instances[i][0]).upper(), sorted_instances[i][1])

    # Create the figure.
    plt.style.use("ggplot")
    fig, ax = plt.subplots(figsize=(15, 8))
    short_instances = sorted_instances[:n_display]

    # Labels.
    y_label = [loader.get_label(s[0]) for s in short_instances]
    y_label.insert(0, "(OTHERS)")
    y = np.arange(len(y_label))

    # Values.
    x = [s[1] for s in short_instances]
    x.insert(0, sum([s[1] for s in sorted_instances[n_display:]]))
    c_map = plt.get_cmap("plasma")
    colors = c_map(1 - y / len(y))
    colors[0] = (0.7, 0.7, 0.7, 1.0)

    # Plot the graph.
    plt.barh(y, x, height=0.5, color=colors)
    ax.set_yticks(y)
    ax.set_yticklabels(y_label)
    ax.invert_yaxis()
    ax.set_title(f"{title}: ({len(samples)} Images)")
    ax.set_xlabel("Count")
    ax.set_ylabel("Class Name")
    plt.savefig(f"{settings.OUTPUT_DIRECTORY}/{file_name}.png")
    plt.clf()


if __name__ == "__main__":

    # Load the project settings and required modules.
    Logger.log_special("Running Sample Analysis", with_gap=True)
    settings = ProjectSettings("settings.yaml")

    # Load the class labels.
    loader = Loader()
    loader.load_labels(settings.LABELS_FILE)

    # Get ALL of the samples in the directory.
    samples = []
    sample_files = os.listdir(settings.SAMPLES_DIRECTORY)
    for i in sample_files:
        file_path = os.path.join(settings.SAMPLES_DIRECTORY, i)
        samples += Loader.load_sample_set_from_file(file_path)

    class_instances = {}
    class_appearances = {}

    for key in loader.label_map:
        class_instances[key] = 0
        class_appearances[key] = 0

    for sample in samples:

        classes_in_sample = {}
        for region in sample.detect_regions:
            class_instances[region.class_id] += 1
            if region.class_id not in classes_in_sample:
                classes_in_sample[region.class_id] = True
                class_appearances[region.class_id] += 1

    display_stats(class_instances, "Instances", "instance_graph", n_display=20)
    display_stats(class_appearances, "Appearances", "appearance_graph", n_display=20)


