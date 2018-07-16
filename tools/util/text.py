# -*- coding: utf-8 -*-

"""
Draw good looking text to Cv2/Numpy images. Cv2's default text renderer is a bit ugly. I can't
specify the font, and not all sizes look great. Here I use PIL with Cv2 to get ttf fonts into the jam,
and also include support for the FontAwesome icon fonts.
"""

import os
from typing import List, Tuple, Dict
import cv2
import numpy as np
from PIL import Image, ImageFont, ImageDraw
from . import visual
from .region import Region

__author__ = "Jakrin Juangbhanich"
__email__ = "juangbhanich.k@gmail.com"

# ======================================================================================================================
# Constants.
# ======================================================================================================================


ALIGN_LEFT = -1
ALIGN_CENTER = 0
ALIGN_RIGHT = 1
ALIGN_TOP = -1
ALIGN_BOTTOM = 1

FONT_DEFAULT = "DEFAULT"
FONT_ICON = "ICON"

DEFAULT_PAD: int = 8


# ======================================================================================================================
# This will manage the PIL TrueType fonts.
# ======================================================================================================================


class TextManager:

    # TODO: I might want to create a way to custom initialize this Singleton.
    # Then I can maybe specify things like custom fonts, etc.

    INSTANCE = None

    def __init__(self):

        self.base_path = os.path.join(os.path.dirname(__file__), "fonts")
        self.fonts_by_size: Dict[int, dict] = {}

        self.font_path_map: Dict[str, str] = {
            FONT_DEFAULT: "RobotoMono-Medium.ttf",
            FONT_ICON: "fa-solid-900.ttf"
        }

        self.font_divisor_map: Dict[str, float] = {
            # Some fonts need a bit more y-offset to look vertically aligned.
            FONT_DEFAULT: 1.6,
            FONT_ICON: 2.0
        }

    @staticmethod
    def instance() -> 'TextManager':
        if TextManager.INSTANCE is None:
            TextManager.INSTANCE = TextManager()
        return TextManager.INSTANCE

    @staticmethod
    def get_font(font_type: str = FONT_DEFAULT, font_size_id: int = 18):
        text_manager = TextManager.instance()
        text_manager._load_font(font_type, font_size_id)
        return text_manager.fonts_by_size[font_size_id][font_type]

    @staticmethod
    def get_font_divisor(font_type: str = FONT_DEFAULT) -> float:
        text_manager = TextManager.instance()
        return text_manager.font_divisor_map[font_type]

    def _load_font(self, font_type: str = FONT_DEFAULT, size: int = 18):
        if size not in self.fonts_by_size:
            self.fonts_by_size[size] = {}

        font_dict = self.fonts_by_size[size]
        if font_type not in font_dict:
            font_path = os.path.join(self.base_path, self.font_path_map[font_type])
            font_dict[font_type] = ImageFont.truetype(font_path, size)


# ===================================================================================================
# Low Level Functions.
# ===================================================================================================


def raw_text(
        image: np.array,
        text: str,
        x: int,
        y: int,
        font_type: str = FONT_DEFAULT,
        font_size: int = 18,
        color=(255, 255, 255)
):
    """ Draw the specified text into the image at the point of the region. """

    # Convert image from CV2 to PIL.
    pil_image, pil_draw = _cv2_to_pil(image)

    # Prepare the font.
    font = TextManager.get_font(font_type=font_type, font_size_id=font_size)

    # Prepare the anchors.
    anchor_x = x
    anchor_y = y

    # Draw the text straight into the region.
    pil_draw.text((anchor_x, anchor_y), text, font=font, fill=(color[2], color[1], color[0]))

    # Convert image from PIL back to CV2.
    final_image = _pil_to_cv2(pil_image)
    return final_image


def raw_icon(
        image: np.array,
        text: str,
        x: int,
        y: int,
        font_size: int = 18,
        color=(255, 255, 255)
):
    """ Write a raw icon to the specified location. """
    return raw_text(image, text, x, y, font_type=FONT_ICON, font_size=font_size, color=color)


def write_icon(
        image: np.array,
        text: str,
        x: int,
        y: int,
        font_size: int = 18,
        color=(255, 255, 255)
):
    """ Write a centered icon at the specific location. """
    i_width, i_height = get_text_size(text, FONT_ICON, font_size)
    x -= i_width // 2
    y -= i_height // 2
    return raw_text(image, text, x, y, font_type=FONT_ICON, font_size=font_size, color=color)


def write_into_region(
        image: np.array,
        text: str,
        region: Region,
        icon: str = None,  # Inline icon to render.
        pad: int = DEFAULT_PAD,
        h_align: int = ALIGN_CENTER,
        font_type: str = FONT_DEFAULT,
        font_size: int = 18,
        color=(255, 255, 255),
        bg_color=None,
        bg_opacity=1.0,
        show_region_outline: bool = False,
        fixed_width: bool = False,  # If the width of the region was fixed from outside. Used to align the icon.
        overlay: bool = False
):
    """ The text will be written into this specified region.
    The y position will be centered. The x position will depend on the align type. """

    # Draw the BG into position.
    image = _fill_region(image, region, bg_color=bg_color, bg_opacity=bg_opacity)

    # If it is overlay, recursive call.
    if overlay:
        sub_sample = np.zeros((image.shape[0], image.shape[1], 3), dtype=np.uint8)
        overlay_image = \
            write_into_region(image=sub_sample, text=text, region=region, icon=icon, pad=pad, h_align=h_align,
                              font_type=font_type, font_size=font_size, color=color, bg_color=(0, 0, 0),
                              bg_opacity=1.0, show_region_outline=False, fixed_width=fixed_width)
        final_image = cv2.addWeighted(image, 1, overlay_image, 1, 0)
        return final_image

    # Use the region to find the position.
    t_width, t_height, i_width, i_height, b_width, b_height = \
        _get_text_and_icon_size(text, icon, pad, font_type, font_size)

    # Default case is central align.
    ix = region.x - b_width // 2
    iy = region.y - i_height // 2
    ty = region.y - int(t_height / TextManager.instance().get_font_divisor(font_type))
    tx = region.x - t_width // 2

    # Left align case.
    if h_align == ALIGN_LEFT or fixed_width:
        ix = region.left if icon is None else region.left + pad

    # Align the text to the icon.
    if h_align == ALIGN_LEFT or (not fixed_width and icon is not None):
        tx = ix + i_width + pad

    # Right align case.
    if h_align == ALIGN_RIGHT:
        ix = region.right - b_width - pad
        tx = ix + i_width + pad if icon is not None else ix

    # Write the text.
    image = raw_text(image=image, text=text, x=tx, y=ty, font_type=font_type, font_size=font_size,
                     color=color)

    if icon is not None:
        image = raw_icon(image=image, text=icon, x=ix, y=iy, font_size=font_size, color=color)

    # Show an outline around the region.
    if show_region_outline:
        cv2.rectangle(image, (region.left, region.top), (region.right, region.bottom), color=(0, 255, 0), thickness=1)

    return image


# ======================================================================================================================
# High Level Functions.
# ======================================================================================================================


def center_at_position(image: np.array, text: str, x: int = 0, y: int = 0, width: int = None, height: int = None,
                       icon: str = None, pad: int = DEFAULT_PAD, font_type: str = FONT_DEFAULT, font_size: int = 18,
                       color=(255, 255, 255), bg_color=(0, 0, 0), bg_opacity=0.5, overlay: bool=False):
    return write_at_position(image=image, text=text, x=x, y=y, width=width, height=height, icon=icon, pad=pad,
                             h_align=ALIGN_CENTER, font_type=font_type, font_size=font_size, color=color,
                             bg_color=bg_color, bg_opacity=bg_opacity, overlay=overlay)


def left_at_position(image: np.array, text: str, x: int = 0, y: int = 0, width: int = None, height: int = None,
                     icon: str = None, pad: int = DEFAULT_PAD, font_type: str = FONT_DEFAULT, font_size: int = 18,
                     color=(255, 255, 255), bg_color=(0, 0, 0), bg_opacity=0.5, overlay: bool=False):
    return write_at_position(image=image, text=text, x=x, y=y, width=width, height=height, icon=icon, pad=pad,
                             h_align=ALIGN_LEFT, font_type=font_type, font_size=font_size, color=color,
                             bg_color=bg_color, bg_opacity=bg_opacity, overlay=overlay)


def write_at_position(
        image: np.array,
        text: str,
        x: int = 0,
        y: int = 0,
        width: int = None,
        height: int = None,
        icon: str = None,
        pad: int = DEFAULT_PAD,
        h_align: int = ALIGN_CENTER,
        font_type: str = FONT_DEFAULT,
        font_size: int = 18,
        color=(255, 255, 255),
        bg_color=None,
        bg_opacity=1.0,
        overlay: bool=False
):
    """ Create a center-locked region, with the specified width and height. """
    region: Region = Region(0, 10, 0, 10)
    is_fixed_width = False

    # Get the meta-data of the text boxes.
    t_width, t_height, i_width, i_height, b_width, b_height = \
        _get_text_and_icon_size(text, icon, pad, font_type, font_size)

    # Finalize the region width and height.
    if width is not None:
        region.width = width
        is_fixed_width = True
    else:
        region.width = b_width
    region.height = height if height is not None else b_height

    # Expand for the padding.
    region.width += pad * 2
    region.height += pad * 2
    region.x = x
    region.y = y

    if h_align == ALIGN_LEFT:
        region.right = x + region.width
        region.left = x

    # Draw the text.
    image = write_into_region(image=image, text=text, region=region, icon=icon, pad=pad, h_align=h_align,
                              font_type=font_type, font_size=font_size, color=color, bg_color=bg_color,
                              bg_opacity=bg_opacity, show_region_outline=False, fixed_width=is_fixed_width,
                              overlay=overlay)

    return image


def write_anchored(image: np.array, text: str, h_anchor: int = ALIGN_CENTER, v_anchor: int = ALIGN_CENTER,
                   icon: str = None, pad: int = DEFAULT_PAD, font_type: str = FONT_DEFAULT, font_size: int = 18,
                   color=(255, 255, 255), bg_color=(0, 0, 0), bg_opacity=1.0, overlay: bool = False):
    """ Find the anchored region and create a text box there. """

    image_width = image.shape[1]
    image_height = image.shape[0]

    x = image_width // 2
    y = image_height // 2

    t_width, t_height, i_width, i_height, b_width, b_height = \
        _get_text_and_icon_size(text, icon, pad, font_type, font_size)

    if h_anchor == ALIGN_LEFT:
        x = pad

    if h_anchor == ALIGN_RIGHT:
        x = image_width - (2 * pad + b_width // 2)

    if v_anchor == ALIGN_TOP:
        y = 2 * pad + b_height // 2

    if v_anchor == ALIGN_BOTTOM:
        y = image_height - (2 * pad + b_height // 2)

    return write_at_position(image=image, text=text, x=x, y=y, width=None, height=None, icon=icon, pad=pad,
                             h_align=h_anchor, font_type=font_type, font_size=font_size, color=color,
                             bg_color=bg_color, bg_opacity=bg_opacity, overlay=overlay)


def label_region(image: np.array, text: str, region: Region, icon: str = None, pad: int = 5, gap: int = 5,
                 font_type: str = FONT_DEFAULT, font_size: int = 14, show_at_bottom: bool=False,
                 color=(255, 255, 255), bg_color=(0, 0, 0), bg_opacity: float = 0.7, overlay: bool = False,
                 inside: bool=False):

    # Find the text, icon and box positions.
    t_width, t_height, i_width, i_height, b_width, b_height = \
        _get_text_and_icon_size(text, icon, pad, font_type, font_size)

    draw_region: Region = region.clone()
    draw_region.height = b_height + pad * 2

    if inside:
        draw_region.width -= gap * 2

    if draw_region.width < b_width + pad * 2:
        draw_region.width = b_width + pad * 2

    draw_direction = -1 if inside else 1
    draw_anchor = draw_region.height // 2 + gap

    # Find the place to draw, relative to the region label.
    if not show_at_bottom:
        y = region.top - (draw_direction * draw_anchor)
    else:
        y = region.bottom + (draw_direction * draw_anchor)

    draw_region.y = y

    return write_into_region(image=image, text=text, region=draw_region, icon=icon, pad=pad, h_align=ALIGN_CENTER,
                             font_type=font_type, font_size=font_size, color=color, bg_color=bg_color,
                             bg_opacity=bg_opacity, show_region_outline=False, fixed_width=True, overlay=overlay)


# ===================================================================================================
# Support Functions.
# ===================================================================================================


def get_text_size(text: str, font_type: str = FONT_DEFAULT, font_size: int = 16):
    """ Returns the width and height for this text, font and size. """
    font = TextManager.get_font(font_type=font_type, font_size_id=font_size)
    return font.getsize(text)


def _get_text_and_icon_size(text: str, icon: str, pad: int = 0, font_type: str = FONT_DEFAULT, font_size: int = 16):
    """ Get the meta-data of the text boxes. """
    t_width, t_height = get_text_size(text, font_type, font_size)
    i_width, i_height = (0, 0) if icon is None else get_text_size(icon, FONT_ICON, font_size)
    b_width, b_height = (t_width, t_height) if icon is None else (t_width + i_width + pad, max(t_height, i_height))
    return t_width, t_height, i_width, i_height, b_width, b_height


def _fill_region(image: np.array, region: Region, bg_color=None, bg_opacity: float = 1.0):
    """ Fill the region in this image with a color and opacity. """

    # No color or opacity is clear, do nothing.
    if bg_color is None or bg_opacity <= 0.0:
        return image

    # Opacity 1, just draw it onto the image.
    if bg_opacity >= 1.0:
        cv2.rectangle(image, (region.left, region.top), (region.right, region.bottom), color=bg_color, thickness=-1)
        return image

    # Opacity is semi-clear. Draw it in a different image and overlay it on.
    overlay_image = np.copy(image)
    cv2.rectangle(overlay_image, (region.left, region.top), (region.right, region.bottom), color=bg_color, thickness=-1)
    return cv2.addWeighted(image, 1.0 - bg_opacity, overlay_image, bg_opacity, 0.0)


def _cv2_to_pil(image: np.array) -> (Image, ImageDraw):
    """ Convert from a PIL ImageDraw to Cv2 Numpy. """
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image)
    image_draw = ImageDraw.Draw(pil_image)
    return pil_image, image_draw


def _pil_to_cv2(image: Image) -> np.array:
    """ Convert from a PIL ImageDraw back to Cv2 Numpy. """
    out_image = np.array(image)
    out_image = cv2.cvtColor(out_image, cv2.COLOR_RGB2BGR)
    return out_image


def _get_aligned_anchor(frame_size: int, text_size: int, align: int, pad: int = 0, position: int = None) -> int:
    """ Find the text anchor position. """

    if align == ALIGN_CENTER:
        if position is None:
            position = frame_size // 2
        return position - text_size // 2

    if align == ALIGN_LEFT:
        if position is None:
            position = 0
        return position + pad

    if align == ALIGN_RIGHT:
        if position is None:
            position = frame_size
        return position - text_size - pad
