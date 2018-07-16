#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The point of this script is to organize all of the bounding box, label, and image data into
a structure called a 'Sample.' The data in its raw form is too big for my shitty PC to
deal with, so I need to break it up into something a bit smaller. I will first ingest all of
the provided data from the CSV files, then create subsets of that data, there the maximum size
of each set will contain 'MAX_SAMPLE_SET_SIZE' images. The Samples will be stored as JSON files
in the desired directory, and we can finally start experimenting with a smaller set of data.
"""

from modules.loader import Loader
from modules.settings import ProjectSettings
from tools.util import pather
from tools.util.logger import Logger

__author__ = "Jakrin Juangbhanich"
__email__ = "juangbhanich.k@gmail.com"

# This is the maximum number of samples that a single 'set' will contain.
MAX_SAMPLE_SET_SIZE = 5000

# Remote URLs
REMOTE_IMAGE_URL_FILE = "https://requestor-proxy.figure-eight.com/figure_eight_datasets/open-images/train-images" \
                        "-boxable.csv "
REMOTE_GROUND_TRUTH_FILE = "https://requestor-proxy.figure-eight.com/figure_eight_datasets/open-images/train" \
                           "-annotations-bbox.csv "


if __name__ == "__main__":

    # Load the project settings and required modules.
    Logger.log_special("Running Sample Creator", with_gap=True)
    settings = ProjectSettings("settings.yaml")
    loader: Loader = Loader()

    # Read in the source data, and create our own sample data.
    Logger.log_special("Begin Sample Initialization", with_gap=True)
    loader.check_and_load(settings.IMAGE_URL_FILE, REMOTE_IMAGE_URL_FILE)
    samples = loader.create_samples(settings.IMAGE_URL_FILE)

    # Now that we have sample IDs and URLs, we can associate them with the GT annotations.
    Logger.log_special("Begin Sample Association", with_gap=True)
    loader.check_and_load(settings.IMAGE_URL_FILE, REMOTE_GROUND_TRUTH_FILE)
    loader.associate_boxes_with_samples(samples, settings.GROUND_TRUTH_FILE)

    # Exporting the created samples.
    Logger.log_special("Begin Sample Export", with_gap=True)
    pather.create(settings.SAMPLES_DIRECTORY)
    loader.export_samples(samples, path=settings.SAMPLES_DIRECTORY, size=5000)

    # All done.
    Logger.log_header("Sample Creation Completed", with_gap=True)

