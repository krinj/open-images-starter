# -*- coding: utf-8 -*-

"""
Use this tool to create, clear, or guarantee that paths exist.
"""

import os
import pathlib
import shutil

__author__ = "Jakrin Juangbhanich"
__email__ = "juangbhanich.k@gmail.com"


def create(path, clear=False):
    """
    Given some arbitrary path, we will create all the directory leading up to it.
    Optionally, we can also clear whatever is there (only at the terminal path).
    """
    _create(path, clear, is_true_tail=True)


def _create(path, clear, is_true_tail):
    head, tail = os.path.split(path)

    # This is the home directory. End it.
    if head == "/" and tail == "":
        return

    # Recursively create the heads.
    if head != "" and head != "~":
        _create(head, clear, is_true_tail=False)

    base, ext = os.path.splitext(tail)
    if ext == "":
        # No extension, this is supposed to be a directory.
        # Clear this if it is the 'head' of the path we are creating.
        if os.path.exists(path) and clear and is_true_tail:
            if path != ".":  # Do NOT attempt to remove the root directory.
                shutil.rmtree(path)

        if not os.path.exists(path):
            pathlib.Path(path).mkdir(parents=True, exist_ok=True)
