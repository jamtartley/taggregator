import glob
import os

def count_lines_in_file(file_name):
    with open(file_name) as f:
        return sum(1 for line in f)

dir_map = {"CODE": "taggregator/*.py", "SCRIPTS": "scripts/*", "TESTS": "tests/*.py"}
total_line_count = 0
dash_count = 40

for header in dir_map.keys():
    print("-" * dash_count)
    print(header)
    print("-" * dash_count)

    for file_name in glob.glob(dir_map[header], recursive=True):
        line_count = count_lines_in_file(file_name)
        total_line_count += line_count
        print("%d\t%s"  %(line_count, file_name))

    print("\n")

print("-" * dash_count)
print("TOTAL: %d" %(total_line_count))
print("-" * dash_count)
