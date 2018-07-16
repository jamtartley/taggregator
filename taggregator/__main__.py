#! /usr/bin/env python3
#! -*- coding: utf-8 -*-

from . import printer
from . import taggregator
from pathlib import Path
import argparse
import os
import sys

class CommandHandler(object):
    def __init__(self):
        parser = argparse.ArgumentParser(description="Search files in a directory for areas with specific tags")
        parser.add_argument("command",  help="Command to run")

        allowed_commands = ["run", "create"]
        self.was_run_by_default = len(sys.argv) <= 1 or sys.argv[1] not in allowed_commands
        command = "run" if self.was_run_by_default else sys.argv[1]

        getattr(self, command)()

    def run(self):
        parser = argparse.ArgumentParser(description="Run the taggregator main program")
        parser.add_argument("root", default="", nargs="?", help="Path from which to start search")
        parser.add_argument("-t", "--tags", help="Comma-separated list of tags to search for (temporarily overrides config file)")
        parser.add_argument("-v", "--verbose", action="store_true", help="Set if program should print verbose output")
        parser.add_argument("--print-headers", action="store_true", help="Set if program should print section headers")
        parser.add_argument("--no-recursion", action="store_true", help="Only look in the given root, do not recursively search children")

        args = parser.parse_args(sys.argv[1:]) if self.was_run_by_default else parser.parse_args(sys.argv[2:])
        taggregator.main(args)

    def create(self):
        # @TODO(LOW) Allow user to specify path for config file
        taggregator.create_default_config_file_current_dir()

def main():
    CommandHandler()

if __name__ == "__main__":
    CommandHandler()
