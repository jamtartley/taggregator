# taggregator

Find lines of source code you have tagged with custom categories, defined inside a ```config.json``` file.

For example, to tag a piece of code which contains a bug, write a comment as below:

```python
do_stuff()
# @BUG(HIGH) buggy_code() throws an unhandled exception!
buggy_code()
do_more_stuff()
```

You can then run ```tagg``` in the project root directory and it will output the file name, line number and description to the console as below.

```
taggregator/taggregator/taggregator.py  :57   # @BUG(HIGH) Throws OSError on some files if in use
taggregator/taggregator/taggregator.py  :64   # @SPEED(MEDIUM) Regex search of processed line
taggregator/taggregator/__main__.py     :34   # @TODO(LOW) Allow user to specify path for config file
```

Each line marked with a tag will be ordered and coloured by priority.
By default, there are a number of tags and priorities in the config file installed.

## Installation

```sh
$ pip3 install --upgrade taggregator
```

Installation will also create a config file at ```~/.taggregator/config.json``` but the program will prioritise a config file stored in ```{current_directory}/.taggregator/config.json``` if it exists.

## Run
### From project root
```sh
$ tagg
```
### From a specified folder
```sh
$ tagg Assets/Scripts
```
### Only return lines marked with "speed" and "refactor"
```sh
$ tagg -t "speed, refactor"
```

## Create config file in current directory
```sh
$ tagg create .
```

## Workflow integration
It might be useful to bind taggregator to a key combination in a tool like vim. For example, place this in your ~/.vimrc:
```
nnoremap <leader>t :!clear;tagg<CR>
```
Presuming your vim leader is ',' you can then access your taggregator todo list at any time by typing ',t' while editing.
