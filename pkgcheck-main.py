#!/usr/bin/python3
# yaourt -S parched-git python-prettytable python3-aur

# validate pkgbuild with namcap
# check for updates using w3watch?
# - or use http://jue.li/crux/ck4up/

# todo:
# - diff versions (wenn in einer zeile strings diffen, dann rot)
# - upstream releases (_watch mit regex)
# - argparse version
# - print summary at the end of the program like
#   x packages scanned, x outdated, x unlinsted, x errors
# - -l arg default val fails while parsing
#   default wird nicht auf 2 gesetzt
# - option: --test-locale / --test-remote. Packete werden in tmp geschoben /
#   heruntergeladen und kompiliert zum test.
# - --ignore <packages>. Liste von Packetnamen, die nicht geprüft werden sollen

import os, re, argparse
from prettytable import PrettyTable # print results in a table
from parched import PKGBUILD # python lib parched parses the PKGBUILDs
from AUR import AUR

packages = dict()
aur_session = AUR()

parser = argparse.ArgumentParser(description='''Scan directory for PKGBUILDs and
                                 check for upstream updates.''')
parser.add_argument('-l', '--level', type=int, default=2, dest='level', nargs=1, help='''recursion depth for the file
                    crawler''')
parser.add_argument('-a', '--all', help='''list all packages,
                    even the up-to-date ones''')
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

def scandir(path, level):
    for (path, dirs, files) in walklevel(path,level):
        if "PKGBUILD" in files:
            path = path+"/PKGBUILD"
            package = PKGBUILD(path)
            for generator in aur_session.aur_info(package.name):
                aurquery = generator

            packages[package.name] = {'filepath': path, 'pkgver':
                                      str(package.version)+"-"+str(package.release)[:-2], 'source': '',
                                      'watchurl': '', 'aurver':
                                      aurquery['Version'], 'upstreamver': '' }
            print_row(package.name)

def compare_versions(packagename):
    localver = packages[packagename]['pkgver'].split("-")
    aurver = packages[packagename]['aurver'].split("-")
    upstreamver = packages[packagename]['upstreamver'].split("-")

    if upstreamver > localver or upstreamver > aurver and upstreamver.len() != 0:
        return 1 # red
    else:
        return 0 # green

def print_row(packagename):
    result = compare_versions(packagename)
    if result == 0:
        print('\033[92m', packagename.ljust(30),
              packages[packagename]['pkgver'].ljust(15),
              packages[packagename]['aurver'].ljust(15),
              packages[packagename]['upstreamver'],'\033[0m')
    else:
        print('\033[93m', packagename.ljust(30),
              packages[packagename]['pkgver'].ljust(15),
              packages[packagename]['aurver'].ljust(15),
              packages[packagename]['upstreamver'],'\033[0m')


print("Name".ljust(30), 
      "Local version".ljust(15),
      "Aur version".ljust(15),
      "Upstream version")

scandir(args.DIR[0], args.level[0])

#text = 'CURRENT_VERSION = "0.4.11.286"' 
#pattern = r'"([0-9\./\\-]*)"'
#print(re.search(pattern, text).group(1))

# hieraus ne klasse zu machen wie z.B. package.print_row() oder
# package.compare_versions() wäre ganz cool
