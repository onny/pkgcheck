#!/usr/bin/python3
# yaourt -S parched-git python3-aur python-requests

# validate pkgbuild with namcap
# - or use http://jue.li/crux/ck4up/

# todo:
# - diff versions (wenn in einer zeile strings diffen, dann rot)
# - upstream releases (_watch mit regex)
# - argparse version
#   unable to call -v alone, DIR still required?
# - print summary at the end of the program like
#   x packages scanned, x outdated, x unlinsted, x errors
# - print stat while scanning
# - option: --test-locale / --test-remote. Packete werden in tmp geschoben /
#   heruntergeladen und kompiliert zum test.
# - --ignore <packages>. Liste von Packetnamen, die nicht geprüft werden sollen
# - packages dict is still empty at the end :/
# - parse flagged out of date in AUR

# _watch='uri','regex'
# wenn kein _watch, dann md5sum auf page
# wenn nur watch uri, dann md5sum auf watchuri
# check return von uri und regex auf versionsnummernsyntax (einzeiler,
# zugelassene zeichen), wenn keine versionsnummer, dann return wert wieder
# md5summen

# write upstreamcheck resuls to .local/share/pkgcheck with
# http://docs.python.org/3.3/library/configparser.html

import os, re, argparse  # filebrowsing, regex, argparse
import hashlib
import requests
from urllib.parse import urlparse
import string
from sys import exit # for the exit statement
#from prettytable import PrettyTable # print results in a table
from parched import PKGBUILD # python lib parched parses the PKGBUILDs
from AUR import AUR # query the AUR with this lib

packages = dict()
aur_session = AUR()

parser = argparse.ArgumentParser(description='''Scan directory for PKGBUILDs and
                                 check for upstream updates.''')
parser.add_argument('-l', '--level', type=int, default=2, dest='level', nargs=1, help='''recursion depth for the file
                    crawler''')
parser.add_argument('-a', '--all', help='list all packages, even the up-to-date ones',
                   action="store_true")
parser.add_argument('-v', '--version', help='print version of pkgcheck', action="store_true")
parser.add_argument('DIR', default='.', nargs=1,
                    help='''directory or file containing PKGBUILD(s)''')

args = parser.parse_args()

version = "0.1"

def url_regex(url, regex):
    try:
        r = requests.get(url)
    except requests.exceptions.MissingSchema:
        return "Malformed url"
    matchObject = re.search(r''+regex, r.text)
    if matchObject:
        return matchObject.group()
    return 0

def url_md5(url):
    try:
        r = requests.get(url)
    except requests.exceptions.MissingSchema:
        return "Malformed url"
    m = hashlib.md5()
    m.update(r.text.encode('utf-8'))
    return m.hexdigest()

def parse_watch(filepath):
    f = open(filepath)
    for line in f:
        p = re.search(r'^\s*_watch\s*=\s*(.*?)$',line) # todo: match until EOL or Hash for commentary
        if p:
            f.close()
            return p.group(1).strip('(|)').split(",") # todo: klammern nur am
                                                      # anfang und ende stipen
    f.close()
    pass

def dummywarn(self,msg):
    pass

class pkgcheck:
    package_count = 0

    def __init__(self, filepath):
        self.filepath = filepath 
        package = PKGBUILD(filepath)

        aur_session.chwarn(dummywarn)
        for generator in aur_session.aur_info(package.name):
            aurquery = generator

        #text = 'CURRENT_VERSION = "0.4.11.286"' 
        #pattern = r'"([0-9\./\\-]*)"'
        #print(re.search(pattern, text).group(1))

        self.pkgname = package.name
        self.pkgver = str(package.version)+"-"+str(package.release)[:-2]
        # todo
        try:
            self.aurver = aurquery['Version']
        except:
            self.aurver = "-"
        if package.url:
            self.url = package.url
        self.watchurl = ""

        watch_params = parse_watch(filepath)
        if watch_params:
            if len(watch_params) == 2:
                self.upstreamver = url_regex(watch_params[0].strip("'"),watch_params[1].strip("'"))
            if len(watch_params) == 1:
                self.upstreamver = url_md5(watch_params[0].strip("'"))
        else:
            if self.url:
                self.upstreamver = url_md5(self.url)
            else:
                self.upstreamver = "unable to check upstream"

        pkgcheck.package_count += 1

    def __del__(self):
        pkgcheck.package_count -= 1

    def check_upstream(self):
        pass
        # todo
        print("check upstream")

    def compare_versions(self):
        if self.upstreamver > self.pkgver or self.upstreamver > self.aurver and str(self.upstreamver).len() != 0:
            return 1 # red
        else:
            return 0 # green

    def print_row(self,state):
        if state:
            print('\033[92m', self.pkgname.ljust(30),
                  self.pkgver.ljust(15),
                  self.aurver.ljust(15),
                  self.upstreamver,'\033[0m')
        else:
            print('\033[93m', self.pkgname.ljust(30),
                  self.pkgver.ljust(15),
                  self.aurver.ljust(15),
                  self.upstreamver,'\033[0m')

    def test_local(self):
        # todo
        pass
        print("test lokal")

    def test_aur(self):
        # todo
        pass
        print("test aur")

    def fetch_aur(self):
        # todo
        pass
        print("fetch aur")

    def fetch_upstream(self):
        # todo
        pass
        print("fetch upstream")

    def push_aur(self):
        # todo
        pass
        print("push aur")

    def push_git(self):
        # todo
        pass
        print("push git")

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
    if os.path.isfile(path):
        package = pkgcheck(path)
        # Print table header
        print("Name".ljust(30), 
              "Local version".ljust(15),
              "Aur version".ljust(15),
              "Upstream version")
        if package.compare_versions() == 0 and args.all:
            package.print_row(1) # print updated, green packages
    else:
        if os.path.exists(path):
            # Print table header
            print("Name".ljust(30), 
                  "Local version".ljust(15),
                  "Aur version".ljust(15),
                  "Upstream version")
            for (path, dirs, files) in walklevel(path,level):
                if "PKGBUILD" in files:
                    path = path+"/PKGBUILD"
                    package = pkgcheck(path)
                    if package.compare_versions() == 0 and args.all:
                        package.print_row(1) # print updated, green packages
                    else:
                        package.print_row(0) # print updated, yellow packages
                    #vars(package)
                    packages = {package}
        else:
            print("File or directory does not exists")

if args.version:
    print("pkgcheck version: "+version)
    exit(0)


# Start scanning the directory for PKGBUILDs
if type(args.level) == list:
    scandir(args.DIR[0], args.level[0])
else:
    scandir(args.DIR[0], args.level)
# todo: print(packages)
