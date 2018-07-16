# -*- coding: utf-8 -*-

"""
Use this to load, save, and display images, samples, and labels.
"""

import csv
import json
import os
import urllib.request
from typing import Dict, List

from modules.detect_region import DetectRegion
from modules.sample import Sample
from modules.settings import ProjectSettings
from tools.util import pather
from tools.util.logger import Logger

__author__ = "Jakrin Juangbhanich"
__email__ = "juangbhanich.k@gmail.com"


class Loader:

    def __init__(self):
        self.label_map: Dict[str, str] = {}

    # ===================================================================================================
    # Labels.
    # ===================================================================================================

    def load_labels(self, path: str = None):
        label_map: Dict[str, str] = {}

        def action(row):
            label_map[row[0]] = row[1]

        self.execute_on_csv(path, action)
        self.label_map = label_map
        return self.label_map

    def get_label(self, key: str, upper: bool=True) -> str:
        if key in self.label_map:
            label = self.label_map[key]
            if upper:
                label = label.upper()
            return label
        return key

    # ===================================================================================================
    # Samples.
    # ===================================================================================================

    @staticmethod
    def load_sample_set(set_index: int) -> List[Sample]:
        """ Load a sample set by index."""
        set_path = os.path.join(
            ProjectSettings.instance().SAMPLES_DIRECTORY,
            f"sample_set_{set_index}.json")
        return Loader.load_sample_set_from_file(set_path)

    @staticmethod
    def load_sample_set_from_file(path: str) -> List[Sample]:
        """ Load the sample set from a path. """
        if not os.path.exists(path):
            raise Exception(f"File {path} doesn't exist! Have you created all the samples first?")

        with open(path, "r") as f:
            data = json.load(f)
            sample_data = data["samples"]
            samples = [Sample.decode(d) for d in sample_data]
            for sample in samples:
                sample.set_index = int(data["set_index"])

        return samples

    def create_samples(self, path) -> Dict[str, Sample]:
        """ Create samples from the rows in the image URL CSV. """
        samples: Dict[str, Sample] = {}

        def action(row):
            sample = Sample()
            sample.key = row[0].split(".")[0]  # Remove the .jpg extension.
            sample.remote_path = row[1]
            samples[sample.key] = sample

        self.execute_on_csv(path, action)
        Logger.log_field("Samples Loaded", len(samples))
        return samples

    def associate_boxes_with_samples(self, samples: Dict[str, Sample], path: str):
        """ Create the detection meta-data for each sample. """
        def action(row):
            key = row[0]
            if key not in samples:
                return

            sample = samples[key]

            x_min = float(row[4])
            x_max = float(row[5])
            y_min = float(row[6])
            y_max = float(row[7])

            detect_region = DetectRegion(force_int=False)
            detect_region.set_rect(x_min, x_max, y_min, y_max)
            detect_region.class_id = row[2]
            detect_region.confidence = float(row[3])
            detect_region.is_occluded = int(row[8])
            detect_region.is_truncated = int(row[9])
            detect_region.is_group_of = int(row[10])
            detect_region.is_depiction = int(row[11])
            detect_region.is_inside = int(row[12])

            sample.detect_regions.append(detect_region)

        self.execute_on_csv(path, action)

    def export_samples(self, samples: Dict[str, Sample], path: str, size: int = 25000):
        """ Break apart a large collection of samples and export them. """
        sample_list = list(samples.values())

        n_samples = len(sample_list)
        i = 0
        while True:
            m = (i + 1) * size
            if m >= n_samples:
                # Lazy breaking, we will miss the final batch.
                break

            sub_samples = sample_list[i * size:m]
            self._write_samples(sub_samples, path, i)
            i += 1

    @staticmethod
    def _write_samples(samples: List[Sample], path: str, index: int):
        """ Write the sample set to a file, with the specified index. """
        file_name = f"sample_set_{index}.json"
        file_path = os.path.join(path, file_name)

        sample_objects = [s.encode() for s in samples]
        sample_data = {
            "set_index": index,
            "samples": sample_objects
        }

        with open(file_path, "w") as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)

    # ===================================================================================================
    # Misc. Support Methods.
    # ===================================================================================================

    @staticmethod
    def check_and_load(path: str, remote_url: str = None) -> None:
        """ Check if the file at the path exists. If not, and remote_url
        is not None, then offer to load it. """

        if not os.path.exists(path):

            print("\nError: File {} does not exist.".format(path))

            if remote_url is not None:
                while True:

                    response = input("Do you want to load it from {}? [y/n]: ".format(remote_url))

                    if response == "y":
                        print("Loading, please wait! (The file is pretty big so this could take a while...)")
                        pather.create(path)
                        urllib.request.urlretrieve(remote_url, path)
                        Logger.log_field("Successfully Loaded", path)

                    if response == "n":
                        break

                    print("Response is not valid. Please enter y or n.\n")

            raise Exception("File not found, unable to proceed.")

    @staticmethod
    def execute_on_csv(path: str, action: classmethod, skip_first_row: bool = False):
        """ Run a specified action on each row of the CSV file. """
        with open(path) as f:

            row_count = sum(1 for _ in f)
            f.seek(0)
            reader = csv.reader(f, delimiter=",")
            Logger.log_field("Reading CSV", os.path.split(path)[1])
            Logger.log_field("Rows", row_count)

            for row in reader:

                # Skip the first row - it is just labels.
                if skip_first_row:
                    skip_first_row = False
                    continue

                action(row)
