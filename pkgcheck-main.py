#!/usr/bin/python3
# yaourt -S parched-git python3-aur python-requests python-xdg

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
# - unable to parse array of pkgbuilds
# - failed to parse: 
    # _watch=('http://www.joomla.org/download.html',' ([\d.]*) Full Package,')
    # ["'http://www.joomla.org/download.html'", "' ([\\d.]*) Full Package", "'"]
# - strict and looseversion:
    # http://stackoverflow.com/questions/1714027/version-number-comparison

# _watch='uri','regex' [done]
# wenn kein _watch, dann md5sum auf page [done]
# wenn nur watch uri, dann md5sum auf watchuri
# check return von uri und regex auf versionsnummernsyntax (einzeiler,
# zugelassene zeichen), wenn keine versionsnummer, dann return wert wieder
# md5summen

import os, re, argparse  # filebrowsing, regex, argparse
import hashlib
import requests
from urllib.parse import urlparse
import string
import configparser # store checksums to .local/share/pkgcheck
import xdg.BaseDirectory as basedir # xdg basedir where to store program data
import time, datetime
from distutils.version import LooseVersion, StrictVersion
    # useful to compare package versions
from sys import exit # for the exit statement
#from prettytable import PrettyTable # print results in a table
from parched import PKGBUILD # python lib parched parses the PKGBUILDs
from AUR import AUR # query the AUR with this lib

packages = dict()
aur_session = AUR()
config = configparser.ConfigParser()

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
        return matchObject.group(1)
    return 0

def url_md5(url):
    try:
        r = requests.get(url)
    except requests.exceptions.MissingSchema:
        return "Malformed url"
    m = hashlib.md5()
    m.update(r.text.encode('utf-8'))
    return m.hexdigest()

def check_md5(pkgname, md5sum):
    ts = time.time()
    if config.read(basedir.xdg_data_home+'/pkgcheck.session'):
        if pkgname in config:
            if config[pkgname]['md5sum'] == md5sum:
                return "not changed since "+datetime.datetime.fromtimestamp(float(config[pkgname]['lastchecked'])).strftime('%Y-%m-%d')
            else:
                return "changed since "+datetime.datetime.fromtimestamp(float(config[pkgname]['lastchecked'])).strftime('%Y-%m-%d')
        else:
            config[pkgname] = {'md5sum': md5sum, 'lastchecked': str(ts)}
            with open(basedir.xdg_data_home+'/pkgcheck.session', 'w') as configfile:
                config.write(configfile)
            return "changed since "+datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    else:
        config[pkgname] = {'md5sum': md5sum, 'lastchecked': str(ts)}
        with open(basedir.xdg_data_home+'/pkgcheck.session', 'w') as configfile:
            config.write(configfile)
        return "changed since "+datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')

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
        try:
            package = PKGBUILD(filepath)
        except ValueError:
            self.pkgname = 'Error parsing file at ' + filepath
            self.pkgver = '-'
            self.aurver = '-'
            self.upstreamver = '-'
            return 
        except TypeError:
            self.pkgname = 'Error parsing file at ' + filepath
            self.pkgver = '-'
            self.aurver = '-'
            self.upstreamver = '-'
            return 
        if type(package.name) == list:
            self.pkgname = 'Error parsing file at ' + filepath
            self.pkgver = '-'
            self.aurver = '-'
            self.upstreamver = '-'
            return 

        aur_session.chwarn(dummywarn)
        for generator in aur_session.aur_info(package.name):
            aurquery = generator

        self.pkgname = package.name
        self.pkgver = str(package.version)+"-"+str(package.release)[:-2]
        # todo
        try:
            self.aurver = aurquery['Version']
        except:
            self.aurver = "-"
        if package.url:
            self.url = package.url
        else:
            self.url = ""
        self.watchurl = ""

        watch_params = parse_watch(filepath)
        if watch_params:
            if len(watch_params) == 2:
                self.upstreamver = url_regex(watch_params[0].strip("'"),watch_params[1].strip("'"))
            if len(watch_params) == 1:
                self.upstreamver = url_md5(watch_params[0].strip("'"))
        else:
            if self.url:
                md5state = check_md5(self.pkgname, url_md5(self.url))
                if md5state:
                    self.upstreamver = md5state
                else:
                    self.upstreamver = md5state
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
        if self.upstreamver > self.pkgver or self.upstreamver > self.aurver and self.upstreamver:
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
            package.print_row(0) # print updated, yellow packages
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
