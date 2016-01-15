import random
import os

def to_utf8(string):
    if isinstance(string, unicode):
        return string.encode('utf-8')
    return string

def to_ascii(string):
    if isinstance(string, unicode):
        return string.encode('ascii', 'replace')
    return string

def shuffle_files(path1, path2):
    print path1
    print path2
    with open(path1) as file1:
        lines1 = file1.readlines()
        n_lines = len(lines1)
        indices = random.sample(range(0, n_lines), n_lines)
        new_lines = []
        for i, line in enumerate(lines1):
            new_lines.insert(indices[i], line)
        with open(path1 + '.tmp', 'w') as temp1:
            temp1.writelines(new_lines)
        with open(path2) as file2:
            new_lines = []
            for i, line in enumerate(file2.readlines()):
                new_lines.insert(indices[i], line)
            with open(path2 + '.tmp', 'w') as temp2:
                temp2.writelines(new_lines)
    os.rename(path1, path1 + '.bak')
    os.rename(path2, path2 + '.bak')
    os.rename(path1 + '.tmp', path1)
    os.rename(path2 + '.tmp', path2)