# Tag Finder

Find lines of source code you have tagged with custom categories, defined inside a ```config.json``` file.

For example, to tag a piece of code which contains a bug, write a comment as below:

```python
do_stuff()
# @BUG(HIGH) buggy_code() throws an unhandled exception!
buggy_code()
do_more_stuff()
```

You can then run ```tagf``` in the project root directory and it will output the file name, line number and description to the console as below.

```
tag_finder/tag_finder/tag_finder.py  :57   # @BUG(HIGH) Throws OSError on some files if in use
tag_finder/tag_finder/tag_finder.py  :64   # @SPEED(MEDIUM) Regex search of processed line
tag_finder/tag_finder/__main__.py    :34   # @TODO(LOW) Allow user to specify path for config file
```

Each line marked with a tag will be ordered and coloured by priority.
By default, there are a number of tags and priorities in the config file installed.

## Installation

```sh
$ pip3 install --upgrade tag-finder
```

Installation will also create a config file at ```~/.tag_finder/config.json``` but the program will prioritise a config file stored in ```{current_directory}/.tag_finder/config.json``` if it exists.

## Run
### From project root
```sh
$ tagf
```
### From a specified folder
```sh
$ tagf Assets/Scripts
```
### Only return lines marked with "speed" and "refactor"
```sh
$ tagf -t "speed, refactor"
```

## Create config file in current directory
```sh
$ tagf create
```

## 
