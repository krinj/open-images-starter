# -*- coding: utf-8 -*-

"""
Library to do some cool visual stuff.
"""

from typing import List, Tuple
import cv2
import numpy as np
import colorsys
from .region import Region

__author__ = "Jakrin Juangbhanich"
__email__ = "juangbhanich.k@gmail.com"


# ======================================================================================================================
# Color Tools.
# ======================================================================================================================


def generate_colors(n,
                    saturation: float = 1.0,
                    brightness: float = 1.0,
                    hue_offset: float = 0.0,
                    hue_range: float = 1.0,
                    as_numpy: bool=False):
    """ Generate N amount of colors spread across a range on the HSV scale.
    Will return it in a numpy format. """
    hsv = [(hue_offset + hue_range * (i / n), saturation, brightness) for i in range(n)]
    colors_raw = list(map(lambda c: colorsys.hsv_to_rgb(*c), hsv))
    colors = np.array(colors_raw)
    colors *= 255

    if not as_numpy:
        colors = [(int(c[0]), int(c[1]), int(c[2])) for c in colors]

    return colors


# TODO: Wish list - Create a colormap system like in CV2, or adapt it so I can create my own color maps.

# ======================================================================================================================
# Region Drawing Tools.
# ======================================================================================================================


def draw_regions(image: np.array,
                 regions: List[Region],
                 color=(255, 255, 255),
                 thickness: int = 2,
                 overlay: bool = False,
                 strength: float = 1.0):

    overlay_image = np.zeros_like(image, np.uint8) if overlay else np.copy(image)

    for i in range(len(regions)):
        r = regions[i]
        cv2.rectangle(overlay_image, (r.left, r.top), (r.right, r.bottom),
                      color=color,
                      thickness=thickness)

    if overlay:
        image = cv2.addWeighted(image, 1.0, overlay_image, strength, 0.0)
    else:
        image = cv2.addWeighted(image, 1.0 - strength, overlay_image, strength, 0.0)

    return image


def pixelate_region(image: np.array, regions: List[Region], blur_factor: float=0.1):
    for r in regions:
        try:
            target_image = safe_extract(image, r.left, r.right, r.top, r.bottom)
            h = target_image.shape[0]
            w = target_image.shape[1]

            pixel_h = max(1, int(h * blur_factor))
            pixel_w = max(1, int(w * blur_factor))

            target_image = cv2.resize(target_image, (pixel_w, pixel_h),
                                      interpolation=cv2.INTER_NEAREST)
            target_image = cv2.resize(target_image, (w, h), interpolation=cv2.INTER_NEAREST)
            image = safe_implant(image, target_image, r.left, r.right, r.top, r.bottom)

        except Exception as e:
            print(e)

    return image


def draw_region_mask(image: np.array, regions: List[Region], strength: float = 1.0):
    """ Apply a mask to the areas covered by the regions. """

    image = image.astype(np.float)
    pos_mask = np.zeros((image.shape[0], image.shape[1]), dtype=np.bool)
    neg_mask = np.ones((image.shape[0], image.shape[1]), dtype=np.bool)

    for r in regions:

        safe_left, safe_right, _, _ = _get_safe_bounds(r.left, r.right, image.shape[1])
        safe_top, safe_bottom, _, _ = _get_safe_bounds(r.top, r.bottom, image.shape[0])

        pos_mask[safe_top:safe_bottom, safe_left:safe_right] = True
        neg_mask[safe_top:safe_bottom, safe_left:safe_right] = False

    fade_factor = 1.0 - (0.7 * strength)
    image[neg_mask] *= fade_factor
    image = image.astype(np.uint8)
    return image


# ======================================================================================================================
# Progress (or custom) Bars.
# ======================================================================================================================


def draw_bar(image, progress: float, x: int, y: int, width: int, height: int,
             frame_color=(0, 0, 0), bar_color=(0, 150, 255)):
    """ Draw a rectangular bar, with the specified progress value filled out. """
    draw_bar_segment(image, 0.0, 1.0, x, y, width, height, frame_color)  # Frame
    draw_bar_segment(image, 0.0, progress, x, y, width, height, bar_color)  # Bar


def draw_bar_segment(image, p_start: float, p_end: float, x: int, y: int, width: int, height: int, color=(0, 150, 255)):
    """ Draw a segment of a bar, for example if we just wanted a start-end section.
    Starting point is the top left. """

    # Draw the bar.
    p_width = max(0.05, p_end - p_start)
    p_width = int(width * p_width)
    p_x = int(x + p_start * width)
    cv2.rectangle(image, (p_x, y), (p_x + p_width, y + height), color, thickness=-1)


# ===================================================================================================
# 2D Image Slice Helpers.
# ===================================================================================================


def _get_safe_bounds(near: int, far: int, max_bound: int) -> (int, int, int, int):
    """ Finds the near/far bounds (such as left, right) for a certain max bound (width, etc). """
    safe_near = max(0, near)
    safe_far = min(max_bound, far)
    near_excess = safe_near - near
    far_excess = far - safe_far
    return safe_near, safe_far, near_excess, far_excess


def safe_extract(image: np.array, left: int, right: int, top: int, bottom: int):
    """ Extract the specified area from the image, padding the over-cropped areas with black.
    Assumes a np.array (CV2 image) input format. """

    safe_left, safe_right, left_excess, right_excess = _get_safe_bounds(left, right, image.shape[1])
    safe_top, safe_bottom, top_excess, bottom_excess = _get_safe_bounds(top, bottom, image.shape[0])

    # Extract the image.
    extracted_image = image[safe_top:safe_bottom, safe_left:safe_right]

    # Get the extraction area.
    h = bottom - top
    w = right - left

    # Fill the excess area with black.
    filler = np.zeros((bottom - top, right - left, 3), dtype=np.uint8)
    insert_bottom = top_excess + h - bottom_excess
    insert_right = left_excess + w - right_excess
    filler[top_excess:insert_bottom, left_excess:insert_right] = extracted_image
    return filler


def safe_implant(dst_image: np.array, src_image: np.array, left: int, right: int, top: int, bottom: int):
    """ Plant the area from the src image into the dst image. """

    # Get the extraction area.
    safe_left, safe_right, left_excess, right_excess = _get_safe_bounds(left, right, dst_image.shape[1])
    safe_top, safe_bottom, top_excess, bottom_excess = _get_safe_bounds(top, bottom, dst_image.shape[0])

    s_bottom = top_excess + (safe_bottom - safe_top)
    s_right = left_excess + (safe_right - safe_left)

    dst_image[safe_top:safe_bottom, safe_left:safe_right] = \
        src_image[top_excess:s_bottom, left_excess:s_right]

    return dst_image


def safe_extract_with_region(image: np.array, region: Region) -> np.array:
    """ Extract the image area specified by the region. """
    return safe_extract(image, region.left, region.right, region.top, region.bottom)


def safe_implant_with_region(dst_image: np.array, src_image: np.array, region: Region) -> np.array:
    """ Plant the area from the src image into the dst image. """
    return safe_implant(dst_image, src_image, region.left, region.right, region.top, region.bottom)
