#!/usr/bin/python3

import os, re, argparse

# todo: -l arg default val fails while parsing

packages = [
    # filepath , pkgname, pkgver, source, watchurl, aurver, upstreamver
]
parser = argparse.ArgumentParser(description='''Scan directory for PKGBUILDs and
                                 check for upstream updates.''')
parser.add_argument('-l', '--level', type=int, default=2, dest='level', nargs=1, help='''recursion depth for the file
                    crawler''')
parser.add_argument('DIR', default='.', nargs=1,
                    help='''directory where to search for PKGBUILD files''')

args = parser.parse_args()

def walklevel(some_dir, level):
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

def scandir(path, level):
    for (path, dirs, files) in walklevel(path,level):
        if "PKGBUILD" in files:
            path = path+"/PKGBUILD"
            packages.append({"filepath": path, "pkgname": "", "pkgver": "", "source": "", "watchurl": "", "aurver": "", "upstreamver": ""})

scandir(args.DIR[0], args.level[0])

for package in packages:
    analyze_pkgbuild(package['filepath'])

#for package in packages:
    #print("path: "+package['filepath'])
