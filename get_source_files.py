import glob

for filename in glob.iglob('src/**/*.txt', recursive=True):
    print(filename);
