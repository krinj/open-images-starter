# -*- coding: utf-8 -*-

"""
Logger Description.
"""

import time
import sys

__author__ = "Jakrin Juangbhanich"
__email__ = "juangbhanich.k@gmail.com"


def non_minimal(f):
    """ Decorator for a logging function that only executes when the logger is not in minimal mode. """
    def func_wrapper(*args, **kwargs):
        if Logger.get_instance().minimal_mode:
            return args[1]
        return f(*args, **kwargs)
    return func_wrapper


class Logger:

    # TODO: Use a decorator for the minimal checking?

    # Character constants (tab, ruler, etc).
    INDENT_CHAR = "   "
    RULER_CHAR = "-"
    BLANK_TAG = "   "
    PROGRESS_BLANK = "▯"
    PROGRESS_FILL = "▮"

    # Color definitions.
    RED = '\33[31m'
    GREEN = '\33[32m'
    YELLOW = '\33[33m'
    BLUE = '\33[34m'
    BOLD = '\33[5m'
    DEFAULT_COLOR = '\33[0m'

    # Singleton instance.
    _INSTANCE = None

    # ==================================================================================================================
    # Public Interface -------------------------------------------------------------------------------------------------
    # ==================================================================================================================

    @staticmethod
    def get_instance() -> "Logger":
        if Logger._INSTANCE is None:
            Logger()
        return Logger._INSTANCE

    @staticmethod
    def log(message, error=False):
        """ Logs a normal message at the indent level, with a timestamp. """
        Logger.get_instance()._log(message, Logger.DEFAULT_COLOR, error=error)

    @staticmethod
    def log_special(message, with_gap=False):
        """ Logs a special (colored) message at the indent level. """
        if with_gap:
            Logger.line_break()
        Logger.get_instance()._log(message, Logger.GREEN)

    @staticmethod
    def log_header(message, with_gap=False):
        """ Logs a special (colored) message at the indent level. """
        if with_gap:
            Logger.line_break()
        Logger.get_instance()._log(message, Logger.YELLOW)

    @staticmethod
    def log_field(field_name, value, extra_indent=1):
        """ Logs a special (colored) message at the indent level. """
        Logger.get_instance()._log_field(field_name, value, False, extra_indent)

    @staticmethod
    def log_field_red(field_name, value, extra_indent=1):
        """ Logs a special (colored) message at the indent level. """
        Logger.get_instance()._log_field(field_name, value, True, extra_indent)

    @staticmethod
    def log_error(message):
        """ Log to the stderr stream. """
        Logger.log(message, error=True)

    @staticmethod
    def line_break(error=False):
        """ Create a horizontal line break. """
        Logger.clear_indent()
        Logger.log("", error)

    @staticmethod
    def line_break_error():
        """ Create a horizontal line break in the stderr stream. """
        Logger.line_break(error=True)

    @staticmethod
    def ruler(length=60):
        """ Creates a ruler of length n, with two line-breaks around it. """
        Logger.line_break()
        Logger.get_instance()._log(Logger.RULER_CHAR * length,
                                   color=Logger.BLUE)
        Logger.line_break()

    @staticmethod
    def ruler_error(length=60):
        """ Creates a ruler of length n, with two line-breaks around it, to the stderr stream. """
        Logger.line_break(error=True)
        Logger.get_instance()._log(Logger.RULER_CHAR * length,
                                   color=Logger.BLUE,
                                   error=True)
        Logger.line_break(error=True)

    @staticmethod
    def indent():
        """ Increase the current indent level by 1. """
        Logger.get_instance()._indent_level += 1

    @staticmethod
    def unindent():
        """ Decrease the current indent level by 1. """
        Logger.get_instance()._indent_level = \
            max(0, Logger.get_instance()._indent_level - 1)

    @staticmethod
    def clear_indent():
        """ Reset the indent level back to 0. """
        Logger.get_instance()._indent_level = 0

    @staticmethod
    def log_progress(percent, header="Progress", suffix=None, extra_indent=1):
        """ Create an animate a progress bar."""
        Logger.get_instance()._log_progress(percent, header, suffix, extra_indent)

    @staticmethod
    def enable_colors():
        """ Turn on color tags. """
        Logger.get_instance()._color_enabled = True

    @staticmethod
    def disable_colors():
        """ Turn off color tags. """
        Logger.get_instance()._color_enabled = False

    @staticmethod
    def enable_minimal_mode():
        """ Turn on minimal mode. """
        Logger.get_instance().minimal_mode = True

    @staticmethod
    def disable_minimal_mode():
        """ Turn off minimal mode. """
        Logger.get_instance().minimal_mode = False

    # ==================================================================================================================
    # Private Methods --------------------------------------------------------------------------------------------------
    # ==================================================================================================================

    def __init__(self):
        self._indent_level = 0
        self._color_enabled = True
        self.minimal_mode = False  # Minimal mode disables headers, indents, progress, colors.
        Logger._INSTANCE = self

    @property
    def color_enabled(self):
        return self._color_enabled and not self.minimal_mode

    def _log_progress(self, percent, header, suffix, extra_indent=1):

        # Cannot process any percent outside of these bounds.
        assert percent >= 0.0
        assert percent <= 1.0

        bar_size = 20
        filled_count = int(percent * bar_size)
        empty_count = bar_size - filled_count
        blue_divider = self._set_color("|", self.BLUE)

        # Create the bar.
        fill_bar = self._set_color(filled_count * self.PROGRESS_FILL, self.GREEN)
        empty_bar = self._set_color(empty_count * self.PROGRESS_BLANK, self.BLUE)
        bar = "{}{}".format(fill_bar, empty_bar)

        # Create the header.
        header = "{}:".format(header)
        header = self._set_color(header, self.BLUE)

        # Create the suffix.
        if suffix is not None:
            suffix = "{} {}".format(blue_divider, suffix)
        else:
            suffix = ""

        # Put it all together.
        formatted_percent = "{:.1f}%".format(percent * 100)

        if self.minimal_mode:
            self._print("{} {} {}".format(header, formatted_percent, suffix))
        else:
            message = "{} {} {} {}".format(header, bar, formatted_percent, suffix)
            message = self._add_format(message, extra_indent)
            message = "\r{}".format(message)
            print(message, end="\r")
            if percent == 1.0:
                print("")

    def _log_field(self, field_name, value, red=False, extra_indent=1):
        field_name = self._set_color("{}:".format(field_name), Logger.BLUE)
        if red:
            value = self._set_color(str(value), Logger.RED)
        message = "{} {}".format(field_name, value)
        self._print(self._add_format(message, extra_indent), False)

    def _log(self, message, color, error=False):
        message = self._set_color(message, color)
        self._print(self._add_format(message), error)

    def _add_format(self, message, extra_indent=0):
        message = self._add_indent(message, extra_indent)
        message = self._add_header(message)
        return message

    @non_minimal
    def _add_indent(self, message, extra_indent):
        return (extra_indent + self._indent_level) * self.INDENT_CHAR + message

    @non_minimal
    def _add_header(self, message):
        return self._get_header() + message

    def _get_header(self):
        header = "{} | ".format(self._get_readable_time(time.localtime()))
        header = self._set_color(header, self.BLUE)
        return header

    def _get_readable_time(self, time_object):
        day = self._pre_fill(time_object.tm_mday)
        date_str = "{}/{}".format(day, time_object.tm_mon)
        hour = self._pre_fill(time_object.tm_hour)
        minute = self._pre_fill(time_object.tm_min)
        time_str = "{}:{}".format(hour, minute)
        final_str = " {} {} ".format(date_str, time_str)
        return final_str

    def _set_color(self, text, color):
        if self.color_enabled:
            return color + text + self.DEFAULT_COLOR
        else:
            return text

    @staticmethod
    def _print(message, error=False):
        if error:
            print(message, file=sys.stderr)
            sys.stderr.flush()
        else:
            print(message)
            sys.stdout.flush()

    @staticmethod
    def _pre_fill(string, length=2, char='0'):
        """ Pad the input string with a fixed amount of chars to the front. """

        # Note: Though this exists in another file, I keep a hard-written version
        # here in case I want to import the logger by itself.
        string = str(string)
        while len(string) < length:
            string = char + string
        return string
