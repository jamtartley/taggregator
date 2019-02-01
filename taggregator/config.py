import json
import os
import pkg_resources
import re
from taggregator import printer
from pathlib import Path
from json.decoder import JSONDecodeError

class UserConfig:
    """
    The idea of this class is to amalgamate data extracted both from the static config file that
    the user maintains as well as the arguments passed in via the command line at runtime.

    It will also validate that the config file is corrrect and not missing any keys as well as
    creating it if it doesn't exist.

    Its main interface is `config_map` which is a dictionary mapping strings to various types
    of data, for example the runtime root, tags to search for, priorities to search for, whether
    the search should be carried out recursively, whether we should display verbose info etc.
    """
    def __init__(self, raw_runtime_args):
        # First we grab everything we can from the config file we find (or create if it doesn't exist)
        self.config_map = self.get_config_map()

        default_config = self.get_default_config_json()

        for key in default_config:
            if key not in self.config_map:
                self.set_config_property(self.config_map, key, default_config[key])

        # We then go on to grab the data from command line arguments that wouldn't have made sense to go in a config file
        self.config_map["root"] = os.getcwd() + "/" + raw_runtime_args.root
        if not self.config_map["root"].endswith("/"):
            self.config_map["root"] += "/"

        self.config_map["is_verbose"] = raw_runtime_args.verbose
        self.config_map["should_recurse"] = not raw_runtime_args.no_recursion

        tags_given_at_runtime = [tag for tag in raw_runtime_args.tags.split(",")] if raw_runtime_args.tags is not None else None
        raw_tags = tags_given_at_runtime if tags_given_at_runtime is not None else self.config_map["tags"]
        self.config_map["tags"] = set([re.escape(tag.strip().upper()) for tag in raw_tags])

    def get_existing_config_path(self):
        """
        Look for existing config in first {current dir}/.taggregator and then .taggregator
        """
        if os.path.isfile(CURRENT_DIR_CONFIG_PATH):
            return CURRENT_DIR_CONFIG_PATH
        else:
            if os.path.isfile(HOME_DIR_CONFIG_PATH):
                return HOME_DIR_CONFIG_PATH

        return None

    def create_default_config_file_current_dir(self):
        self.create_default_config_file(CURRENT_DIR_CONFIG_FOLDER)

    def create_default_config_file(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)
            printer.log("Creating config directory at: " + directory, "information")

        path = directory + CONFIG_FILE_NAME

        if os.path.exists(path):
            while True:
                answer = input("[WARNING] File already exists, do you wish to overwrite it? (y/n): ").lower().strip()
                if answer == "y":
                    self.copy_default_config_to_path(path)
                    return path
                elif answer == "n":
                    return None

        self.copy_default_config_to_path(path)
        return path

    def copy_default_config_to_path(self, path):
        default_config_json = self.get_default_config_json()
        printer.log("Creating config file at: " + path, "information")

        with open(path, "w") as config_file:
            json.dump(default_config_json, config_file, indent=4)

    def get_default_config_json(self):
        with open(pkg_resources.resource_filename(__name__, "default_config.json"), encoding="utf-8") as default_config_file:
            return json.loads(default_config_file.read())

    def get_config_map(self):
        """
        Return the content of a config.json if one is found.
        If not, one is created.
        """
        # If neither ~/.taggregator or {current dir}/.taggregator exists,
        # create ~/.taggregator and copy in the default config file from bundle resources
        config_path = self.get_existing_config_path()

        if config_path:
            printer.verbose_log("Config found at: " + config_path, "information", append_new_line=True)
        else:
            printer.log("No config file found!", "warning")
            config_path = self.create_default_config_file(HOME_DIR_CONFIG_PATH)

        try:
            with open(config_path) as config_json:
                return json.load(config_json)
        except JSONDecodeError as je:
            error_string = "Error in your taggregator config file at line %d, column %d, exiting..." %(je.lineno, je.colno)
            printer.log(error_string, "fatal error")
            raise SystemExit()

    def set_config_property(self, config, key, value):
        config[key] = value
        config_path = self.get_existing_config_path()

        printer.log("Found unset config property: '%s', setting it to '%s'" %(key, value), "warning")

        with open(config_path, "w") as config_file:
            json.dump(config, config_file, indent=4)

CONFIG_FOLDER = "/.taggregator/"
CONFIG_FILE_NAME = "config.json"
CURRENT_DIR_CONFIG_FOLDER = os.getcwd() + CONFIG_FOLDER
CURRENT_DIR_CONFIG_PATH = CURRENT_DIR_CONFIG_FOLDER + CONFIG_FOLDER
HOME_DIR_CONFIG_FOLDER = str(Path.home()) + CONFIG_FOLDER
HOME_DIR_CONFIG_PATH = HOME_DIR_CONFIG_FOLDER + CONFIG_FILE_NAME
