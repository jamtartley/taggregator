#! /usr/bin/env python3
#! -*- coding: utf-8 -*-

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
    of data, for example the runtime root, tags to search for, priorities to search for etc.
    """
    def __init__(self, raw_runtime_args):
        # First we grab everything we can from the config file we find (or create if it doesn't exist)
        self.config_map = get_config_map()

        default_config = get_default_config_json()

        for key in default_config:
            if key not in self.config_map:
                set_config_property(self.config_map, key, default_config[key])

        # We then go on to grab the data from command line arguments that wouldn't have made sense to go in a config file
        self.config_map["root"] = os.path.abspath(raw_runtime_args.root)

        # If we were passed in a set of tags at runtime they take
        # priority and we use them, falling back to tags in config file.
        tags_given_at_runtime = [tag for tag in raw_runtime_args.tags.split(",")] if raw_runtime_args.tags is not None else None
        tags_to_use = tags_given_at_runtime if tags_given_at_runtime is not None else self.config_map["tags"]
        self.config_map["tags"] = set([re.escape(tag.strip().upper()) for tag in tags_to_use])

def get_existing_config_path():
    """
    Look for existing config in first {current dir}/.taggregator and then ~/.taggregator
    """
    current_dir_path = os.path.join(os.getcwd(), os.path.join(CONFIG_FOLDER, CONFIG_FILE_NAME))

    if os.path.isfile(current_dir_path):
        return current_dir_path
    else:
        if os.path.isfile(HOME_DIR_CONFIG_PATH):
            return HOME_DIR_CONFIG_PATH

    return None

def copy_default_config_to_path(path):
    default_config_json = get_default_config_json()
    printer.log("Creating config file at: " + path, "information")

    with open(path, "w") as config_file:
        json.dump(default_config_json, config_file, indent=4)

def get_default_config_json():
    with open(pkg_resources.resource_filename(__name__, "default_config.json"), encoding="utf-8") as default_config_file:
        return json.loads(default_config_file.read())

# @CLEANUP(LOW) get_config_map is a misleading name
# It has the side effect of creating a config file
# if one doesn't exist, but the name implies purity.
def get_config_map():
    """
    Return the content of a config.json if one is found.
    If not, one is created.
    """
    # If neither ~/.taggregator or {current dir}/.taggregator exists,
    # create ~/.taggregator and copy in the default config file from bundle resources
    config_path = get_existing_config_path()

    if not config_path:
        printer.log("No config file found!", "warning")
        config_path = create_default_config_file(HOME_DIR_CONFIG_PATH)

    try:
        with open(config_path) as config_json:
            return json.load(config_json)
    except JSONDecodeError as je:
        error_string = "Error in your taggregator config file at line %d, column %d, exiting..." %(je.lineno, je.colno)
        printer.log(error_string, "fatal error")
        raise SystemExit()

def set_config_property(config, key, value):
    config[key] = value
    config_path = get_existing_config_path()

    printer.log("Found unset config property: '%s', setting it to '%s'" %(key, value), "warning")

    with open(config_path, "w") as config_file:
        json.dump(config, config_file, indent=4)

def create_default_config_file(directory):
    dir_path = os.path.join(directory, ".taggregator")

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        printer.log("Creating config directory at: " + dir_path, "information")

    path = os.path.join(dir_path, CONFIG_FILE_NAME)

    if os.path.exists(path):
        while True:
            answer = input("[WARNING] File already exists, do you wish to overwrite it? (y/n): ").lower().strip()
            if answer == "y":
                copy_default_config_to_path(path)
                return path
            elif answer == "n":
                return None

    copy_default_config_to_path(path)
    return path


CONFIG_FOLDER = ".taggregator"
CONFIG_FILE_NAME = "config.json"
HOME_DIR_CONFIG_FOLDER = os.path.join(str(Path.home()), CONFIG_FOLDER)
HOME_DIR_CONFIG_PATH = os.path.join(HOME_DIR_CONFIG_FOLDER, CONFIG_FILE_NAME)
