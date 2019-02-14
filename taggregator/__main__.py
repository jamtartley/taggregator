#! /usr/bin/env python3
#! -*- coding: utf-8 -*-

from taggregator import config
from taggregator import printer
from taggregator import tagg
import argparse
import os
import sys
import cProfile, pstats, io

class ProfileData:
    def __init__(self, should_do_profiling, line_count, sort_by):
        self.should_do_profiling = should_do_profiling
        self.line_count = line_count # How many lines the printout should display
        self.sort_by = sort_by

class CommandHandler:
    def __init__(self, profile_data):
        self.profile_data = profile_data

        parser = argparse.ArgumentParser(description="Search files in a directory for areas with specific tags")
        parser.add_argument("command",  help="Command to run")

        allowed_commands = ["run", "create"]
        self.was_run_by_default = len(sys.argv) <= 1 or sys.argv[1] not in allowed_commands
        command = "run" if self.was_run_by_default else sys.argv[1]

        getattr(self, command)()

    def run(self):
        if self.profile_data.should_do_profiling:
            pr = cProfile.Profile()
            pr.enable()

        parser = argparse.ArgumentParser(description="Run the taggregator main program")
        parser.add_argument("root", default="", nargs="?", help="Path from which to start search")
        parser.add_argument("-t", "--tags", help="Comma-separated list of tags to search for (temporarily overrides config file)")

        raw_args = parser.parse_args(sys.argv[1:]) if self.was_run_by_default else parser.parse_args(sys.argv[2:])
        user_config = config.UserConfig(raw_args)

        tagg.run(user_config.config_map)

        if self.profile_data.should_do_profiling:
            pr.disable()
            s = io.StringIO()
            ps = pstats.Stats(pr, stream=s).sort_stats(self.profile_data.sort_by)
            ps.print_stats()

            for i, line in enumerate(s.getvalue().split('\n')):
                if (i < self.profile_data.line_count):
                    print(line)

    def create(self):
        parser = argparse.ArgumentParser(description="Run the taggregator config file creator")
        parser.add_argument("root", default="", nargs="?", help="Directory in which to create config folder")
        raw_args = parser.parse_args(sys.argv[1:]) if self.was_run_by_default else parser.parse_args(sys.argv[2:])

        config.create_default_config_file(raw_args.root)

def main():
    CommandHandler(profile_data)

if __name__ == "__main__":
    CommandHandler(profile_data)

profile_data = ProfileData(False, 30, 'tottime')
