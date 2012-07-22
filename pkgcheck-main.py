#!/usr/bin/python3

import os, re

# todo: path arg

level = 2 # recursion depth
packages = [
    # filepath , pkgname, pkgver, source, watchurl, aurver, upstreamver
]

def walklevel(some_dir, level=1):
    some_dir = some_dir.rstrip(os.path.sep)
    assert os.path.isdir(some_dir)
    num_sep = some_dir.count(os.path.sep)
    for root, dirs, files in os.walk(some_dir):
        yield root, dirs, files
        num_sep_this = root.count(os.path.sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]

def analyze_pkgbuild(filepath):
    print(filepath)

def scandir(path):
    for (path, dirs, files) in walklevel(path,level):
        if "PKGBUILD" in files:
            path = path+"/PKGBUILD"
            packages.append({"filepath": path, "pkgname": "", "pkgver": "", "source": "", "watchurl": "", "aurver": "", "upstreamver": ""})

scandir("../aur-packets/")

for package in packages:
    analyze_pkgbuild(package['filepath'])

#for package in packages:
    #print("path: "+package['filepath'])
