# -*- coding: utf-8 -*-

"""
A single instance of a detection for an image.
"""

from tools.util.region import Region

__author__ = "Jakrin Juangbhanich"
__email__ = "juangbhanich.k@gmail.com"


class DetectRegion(Region):
    def __init__(self, left=0, right=0, top=0, bottom=0, force_int: bool = True):
        super().__init__(left, right, top, bottom, force_int)

        # Detection meta-data.
        self.class_id: str = None
        self.confidence: float = 1.0
        self.is_occluded: int = 0
        self.is_truncated: int = 0
        self.is_group_of: int = 0
        self.is_depiction: int = 0
        self.is_inside: int = 0

    def encode(self) -> dict:
        data = {
            "left": self.left,
            "right": self.right,
            "top": self.top,
            "bottom": self.bottom,
            "class_id": self.class_id,
            "confidence": self.confidence,
            "is_occluded": self.is_occluded,
            "is_truncated": self.is_truncated,
            "is_group_of": self.is_group_of,
            "is_depiction": self.is_depiction,
            "is_inside": self.is_inside
        }
        return data

    @staticmethod
    def decode(data: dict) -> 'DetectRegion':
        region = DetectRegion(force_int=False)
        region.left = float(data["left"])
        region.right = float(data["right"])
        region.top = float(data["top"])
        region.bottom = float(data["bottom"])
        region.class_id = str(data["class_id"])
        region.confidence = float(data["confidence"])
        region.is_occluded = int(data["is_occluded"])
        region.is_truncated = int(data["is_truncated"])
        region.is_group_of = int(data["is_group_of"])
        region.is_depiction = int(data["is_depiction"])
        region.is_inside = int(data["is_inside"])
        return region
