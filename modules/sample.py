# -*- coding: utf-8 -*-

"""
A training/testing image sample.
"""

import os
import shutil
import urllib.request
from typing import List
import cv2
from modules.detect_region import DetectRegion
from modules.settings import ProjectSettings
from tools.util import pather, visual
from tools.util.logger import Logger
from tools.util.region import Region

__author__ = "Jakrin Juangbhanich"
__email__ = "juangbhanich.k@gmail.com"


class Sample:

    def __init__(self):
        self.key: str = ""  # Unique ID for this image.
        self.set_index: int = None  # Index of the set this sample belongs to.
        self.remote_path: str = ""
        self.detect_regions: List[DetectRegion] = []
        self._local_path = None

    @property
    def is_locally_loaded(self):
        """ Has the image for this sample been downloaded locally? """
        return os.path.exists(self._local_image_path)

    def load(self):
        """ Load the image for this sample into the designated storage file."""
        Logger.log_field("Loading Image", self.key)
        try:
            pather.create(self._local_image_path)
            urllib.request.urlretrieve(self.remote_path, self._local_image_path)
        except Exception as e:
            Logger.log_field("Loading Failed", e)
        Logger.log_field("Loading Complete", self.key)

    @property
    def image(self):
        """ Get the CV2 image for this sample (BGR Format). """
        if not self.is_locally_loaded:
            self.load()

        try:
            return cv2.imread(self._local_image_path)
        except Exception as e:
            Logger.log_field(f"Error Loading Image {self.key}", e)
            os.remove(self._local_image_path)
            exit(1)

    @property
    def _local_image_path(self):
        """ Get the local image path for this sample. """
        if self._local_path is None:
            self._local_path = os.path.join(
                self.get_set_path(self.set_index),
                f"{self.key}.jpg")
        return self._local_path

    @staticmethod
    def get_set_path(set_index: int) -> str:
        """ Get the storage path for the specified set index."""
        return os.path.join(
            ProjectSettings.instance().STORAGE_DIRECTORY,
            "sample_images",
            f"set_{set_index}")
    
    # ===================================================================================================
    # Visualization.
    # ===================================================================================================

    def get_visualized_image(self,
                             detect_regions: List[DetectRegion]=None,
                             label_map_function: classmethod=None):
        """ Draw the bounding boxes and labels for the detected regions."""
        image = self.image
        w = image.shape[1]
        h = image.shape[0]

        class_label_regions = {}
        color_map = {}

        # If not specified, set the detect regions to the class instance.
        if detect_regions is None:
            detect_regions = self.detect_regions

        # Create a color map for all the labels.
        for region in detect_regions:
            label = label_map_function(region.class_id) if label_map_function is not None else region.class_id
            color_map[label] = None

        colors = visual.generate_colors(len(color_map), saturation=0.8, hue_offset=0.35, hue_range=0.5)

        i = 0
        for key in color_map.keys():
            color_map[key] = colors[i]
            i += 1

        for region in detect_regions:

            # Convert the relative region to pixel coordinates.
            pixel_region = Region(
                left=int(region.left * w),
                right=int(region.right * w),
                top=int(region.top * h),
                bottom=int(region.bottom * h)
            )

            # Get the label and color.
            class_label = label_map_function(region.class_id) if label_map_function is not None else region.class_id
            color = color_map[class_label]

            # Draw the bounding boxes.
            image = visual.draw_regions(image, [pixel_region], color=(0, 0, 0), thickness=10, strength=0.3)
            image = visual.draw_regions(image, [pixel_region], color=color, thickness=4, overlay=True)

            # Tag the label.
            if class_label not in class_label_regions:
                class_label_regions[class_label] = pixel_region
            elif class_label_regions[class_label].width < pixel_region.width:
                class_label_regions[class_label] = pixel_region

        # Draw the rest of the labels on.
        for label, region in class_label_regions.items():
            label_inside = region.top <= 30
            from tools.util import text
            image = text.label_region(image, label, region, color=color_map[label],
                                      bg_opacity=0.7, overlay=True, font_size=20, inside=label_inside)

        return image

    # ===================================================================================================
    # Serialization.
    # ===================================================================================================

    def encode(self) -> dict:
        """ Convert this sample into a Dictionary object. """
        region_data = [r.encode() for r in self.detect_regions]

        data = {
            "key": self.key,
            "remote_path": self.remote_path,
            "detect_regions": region_data
        }

        return data

    @staticmethod
    def decode(data: dict) -> 'Sample':
        """ Decode a JSON dict into a Sample. """

        sample = Sample()
        sample.key = data["key"]
        sample.remote_path = data["remote_path"]
        sample.detect_regions = [DetectRegion.decode(d) for d in data["detect_regions"]]
        return sample
