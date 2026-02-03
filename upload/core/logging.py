# This file is based on the original file "core.py" from the project:
#
# "ESPlog" by armanghobadi
#   https://github.com/armanghobadi/ESPlog/tree/main
#
# Original code copyright: (c) 2024 Arman Ghobadi.
# Licensed under the MIT License (see below).
#
# My modifications: (c) 2025 Tomasz Wojtasek 
# Description of changes:
# - Transformed Logger class into python-style module singleton
# - Added function "exception" to log exception messages.
# TO-DO:
# - zoptymalizować operacje logowanie do plików poprzez buforowanie
#   można np. ciągle zapisywać do RAM i udostępniać metodę get_buffer_size,
#   który zwróci rozmiar zapisanych logów.
#   Do zapisu logów udostępnić metodę "flush" (tzw. explicit flush).
#   Można by wywoływać tą metodę, gdy kontrolery są w stanie idle - gdy nie ma
#   aktualnie ważnych operacji do wykonania.
#
#   Przemyśl sytuacje w których:
#       - bufor się zbyt mocno przepełni
#       - dodanie logów z bufora spowoduje przekroczenie limitu rozmiaru pliku
#
# - Separate Logger.level variable into two levels, one for console and one for filesystem.
#
#
# ------------------------------------------------------------------------------
# MIT License
#
# Copyright (c) 2024 Arman Ghobadi,
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ------------------------------------------------------------------------------
#

import time
import os
import ujson

class _Logger:
    # Define log levels
    LEVELS = {
        "DEBUG": 0,
        "INFO": 1,
        "WARNING": 2,
        "ERROR": 3,
        "CRITICAL": 4,
        "TRACE": -1
    }

    COLORS = {
        "DEBUG": "\033[94m",   # Blue
        "INFO": "\033[92m",    # Green
        "WARNING": "\033[93m", # Yellow
        "ERROR": "\033[91m",   # Red
        "CRITICAL": "\033[41m", # Red background
        "TRACE": "\033[37m",   # White
        "RESET": "\033[0m"     # Reset color
    }

    def __init__(self, level="INFO", log_to_console=True, log_to_file=False, file_name="log.txt", max_file_size=0, use_colors=True, log_format="text"):
        """
        Initialize the Logger.
        :param level: Default log level (DEBUG, INFO, WARNING, ERROR)
        :param log_to_console: Whether to output logs to the console
        :param log_to_file: Whether to save logs to a file
        :param file_name: Name of the log file if log_to_file is True
        :param max_file_size: Maximum log file size in bytes before rotation (0 = no limit)
        :param use_colors: Whether to use colored output for console logs
        :param log_format: The format to store logs ("text" or "json")
        """
        self.current_level = self.LEVELS.get(level.upper(), 1)
        self.log_to_console = log_to_console
        self.log_to_file = log_to_file
        self.file_name = file_name
        self.max_file_size = max_file_size
        self.use_colors = use_colors
        self.log_format = log_format
        self._buffer = [] # buffer for logs that will be saved into filesystem.

        if self.log_to_file:
            # Initialize log file with proper format
            if self.log_format == "json":
                # Create an empty JSON array if it's a new file
                try:
                    with open(self.file_name, "w") as f:
                        ujson.dump([], f)  # Start with an empty list for JSON logs
                except OSError as e:
                    print(f"Error initializing log file: {e}")
            else:
                with open(self.file_name, "w") as f:
                    f.write("Logger initialized.\n")

    def set_level(self, level):
        """Set the logging level.""" 
        self.current_level = self.LEVELS.get(level.upper(), 1)

    def _format_timestamp(self):
        """Generate a timestamp in the format: YYYY-MM-DD HH:MM:SS."""
        current_time = time.localtime()
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            current_time[0], current_time[1], current_time[2],
            current_time[3], current_time[4], current_time[5]
        )

    def _rotate_file(self):
        """Rotate the log file if it exceeds the max size."""
        if self.max_file_size > 0:
            try:
                with open(self.file_name, "r") as f:
                    f.seek(0, 2)  # Move to the end of the file
                    file_size = f.tell()  # Get the current position (file size)
                if file_size > self.max_file_size:
                    os.rename(self.file_name, self.file_name + ".old")
                    with open(self.file_name, "w") as f:
                        if self.log_format == "json":
                            ujson.dump([], f)  # Reset JSON to an empty array
                        else:
                            f.write("Log rotated.\n")
            except OSError:
                pass

    def _log(self, level, message):
        """Core logging method."""
        if self.LEVELS[level] >= self.current_level:
            timestamp = self._format_timestamp()
            log_message = {
                "timestamp": timestamp,
                "level": level,
                "message": message
            }

            if self.use_colors and level in self.COLORS:
                log_message["color"] = self.COLORS[level]  # Save color info for console output

            if self.log_to_console:
                # Output formatted message to console
                console_message = f"[{timestamp}][{level}] {message}"
                if self.use_colors and level in self.COLORS:
                    console_message = f"{self.COLORS[level]}{console_message}{self.COLORS['RESET']}"
                print(console_message)

            if self.log_to_file:
                self._buffer.append(log_message) # musze się zastanowic w jakiej kolejnosci doda logi.
                
                # -----------------------------------------------------------
                # STARY KOD - jeszcze go przetestuj czy rzeczywiscie spowalnia
                # -----------------------------------------------------------
                # self._rotate_file()
                # try:
                #     # Read the existing logs from the file
                #     with open(self.file_name, "r") as f_read:
                #         logs = ujson.load(f_read)
                #     # Append the new log message
                #     logs.append(log_message)
                #     # Write back the updated logs
                #     with open(self.file_name, "w") as f_write:
                #         ujson.dump(logs, f_write)  # Write the updated log entries as JSON
                # except OSError as e:
                #     print(f"Error writing to log file: {e}")
                # except ValueError:
                #     # If file content is not valid JSON (e.g., empty or corrupt), create a new list
                #     with open(self.file_name, "w") as f_write:
                #         ujson.dump([log_message], f_write)

    def debug(self, message):
        """Log a message at DEBUG level."""
        self._log("DEBUG", message)

    def info(self, message):
        """Log a message at INFO level."""
        self._log("INFO", message)

    def warning(self, message):
        """Log a message at WARNING level."""
        self._log("WARNING", message)

    def error(self, message):
        """Log a message at ERROR level."""
        self._log("ERROR", message)

    def exception(self, e: Exception):
        """Log an exception with full traceback at ERROR level."""
        self._log("ERROR", e)
        # wersja robocza!!!
        import sys
        sys.print_exception(e)

    def critical(self, message):
        """Log a message at CRITICAL level."""
        self._log("CRITICAL", message)

    def trace(self, message):
        """Log a message at TRACE level."""
        self._log("TRACE", message)

    # Modified function disable() and added new function enable() / Zogir

    def disable(self):
        """Completely disable all logging."""
        self._enabled_level = self.current_level  # zapamiętaj aktualny poziom
        self.current_level = float("inf")

    def enable(self, level=None):
        """
        Enable logging. 
        If `level` is provided, set this as the current level. 
        Otherwise, restore previous level before disable() or default to INFO.
        """
        if level is not None:
            self.current_level = self.LEVELS.get(level.upper(), 1)
        elif hasattr(self, "_enabled_level"):
            self.current_level = self._enabled_level
        else:
            self.current_level = self.LEVELS["INFO"]

    def get_buffer_size(self):
        """ Return length of log buffer that need to be saved into filesystem. """
        return len(self._buffer)

    def flush(self):
        """ Flush the log buffer into filesystem. """
        self._rotate_file()
        try:
            # Read the existing logs from the file
            with open(self.file_name, "r") as f_read:
                logs = ujson.load(f_read)
            # Append log messages
            for log_msg in self._buffer:
                logs.append(log_msg)
            self._buffer.clear()
            # Write back the updated logs
            with open(self.file_name, "w") as f_write:
                ujson.dump(logs, f_write)  # Write the updated log entries as JSON
        except OSError as e:
            print(f"Error writing to log file: {e}")
        except ValueError:
            # If file content is not valid JSON (e.g., empty or corrupt), create a new list
            with open(self.file_name, "w") as f_write:
                ujson.dump([log_message], f_write)

    def clear_logs(self):
        # Another idea
        pass

        

# Python-like module singleton
# -------------------------------------------------------------

logger = _Logger(
    level="DEBUG",  
    log_to_console=True, 
    log_to_file=False,
    file_name="log.txt",
    max_file_size=1024,
    use_colors=True,
    log_format="text"
)        

# -------------------------------------------------------------