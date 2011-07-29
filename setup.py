#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import glob
import subprocess
from stat import *
from distutils.core import setup
from distutils.command.install import install as _install
from distutils.command.install_data import install_data as _install_data

INSTALLED_FILES = "installed_files"

from spectlib import __pkg_version__ as version

def give_files(dir, *extension):
    files=[]
    all_files=os.listdir(dir)
    for file in all_files:
        ext=(os.path.splitext(file))[1]
        if ext in extension:
            files.append(dir + file)
    return files

class install (_install):

    def run (self):
        _install.run (self)
        outputs = self.get_outputs()
        length = 0
        if self.root:
            length += len (self.root)
        if self.prefix:
            length += len (self.prefix)
        if length:
            for counter in xrange (len (outputs)):
                outputs[counter] = outputs[counter][length:]
        data = "\n".join (outputs)
        try:
            file = open (INSTALLED_FILES, "w")
        except:
            self.warn ("Could not write installed files list %s" % \
                       INSTALLED_FILES)
            return 
        file.write (data)
        file.close ()

class install_data (_install_data):

    def run (self):
        def chmod_data_file (file):
            try:
                os.chmod (file, S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH)
            except:
                self.warn ("Could not chmod data file %s" % file)
        _install_data.run (self)
        map (chmod_data_file, self.get_outputs ())

class uninstall (_install):

    def run (self):
        try:
            file = open (INSTALLED_FILES, "r")
        except:
            self.warn ("Could not read installed files list %s" % \
                       INSTALLED_FILES)
            return 
        files = file.readlines ()
        file.close ()
        prepend = ""
        if self.root:
            prepend += self.root
        if self.prefix:
            prepend += self.prefix
        if len (prepend):
            for counter in xrange (len (files)):
                files[counter] = prepend + files[counter].rstrip ()
        for file in files:
            print "Uninstalling %s" % file
            try:
                os.unlink (file)
            except:
                self.warn ("Could not remove file %s" % file)

ops = ("install", "build", "sdist", "uninstall", "clean")

if len (sys.argv) < 2 or sys.argv[1] not in ops:
    print "Please specify operation : %s" % " | ".join (ops)
    raise SystemExit


if sys.argv[1] in ("build", "install"):
    prefix = None
    if len (sys.argv) > 2:
        i = 0
        for o in sys.argv:
            if o.startswith ("--prefix"):
                if o == "--prefix":
                    if len (sys.argv) >= i:
                        prefix = sys.argv[i + 1]
                    sys.argv.remove (prefix)
                elif o.startswith ("--prefix=") and len (o[9:]):
                    prefix = o[9:]
                sys.argv.remove (o)
                break
            i += 1
    if not prefix and "PREFIX" in os.environ:
        prefix = os.environ["PREFIX"]
    if not prefix or not len (prefix):
        prefix = "/usr/local"

    if sys.argv[1] in ("install", "uninstall") and len (prefix):
#    if len (prefix):
        sys.argv += ["--prefix", prefix]

    if sys.argv[1] == "build":
        with open(os.path.join("data/indicator/specto.in"), "rt") as file_in:
            data = file_in.read()
            data = data.replace("@prefix@", prefix)
            with open (os.path.join ("data/indicator/specto"), "wt") as file_out:
                file_out.write(data)

        cmd = "intltool-merge -d -u po/ data/desktop/specto.desktop.in specto.desktop".split(" ")
        try:
            proc = subprocess.Popen(cmd)
            proc.wait()
        except:
            print "Error: intltool-merge not found, please install the intltool package."
            raise SystemExit

custom_images = []

data_files = [
    ("share/applications", ["specto.desktop"]),
    ("share/doc/specto", ["AUTHORS", "COPYING"]),
    ('share/specto/uis', give_files('data/uis/', '.ui')),
    ('share/indicators/messages/applications', ['data/indicator/specto'])
]

global_icon_path = "share/icons/hicolor"
local_icon_path = "share/specto/icons/hicolor/"

if sys.argv[1] in ("build", "install"):
    for dir, subdirs, files in os.walk("data/icons/"):
        if dir == "data/icons/":
            for file in files:
                custom_images.append(dir + file)
        else:
            images = []
            global_images = []

            for file in files:
                if file.find(".svg") or file.find(".png"):
                    file_path = "%s/%s" % (dir, file)
                    # global image
                    if file[:-4] == "specto":
                        global_images.append(file_path)
                    # local image
                    else:
                        images.append(file_path)
            # local
            if len(images) > 0:
                data_files.append((local_icon_path + dir[10:], images))
            # global
            if len(global_images) > 0:
                data_files.append((global_icon_path + dir[10:], global_images))

    data_files.append(("share/specto/icons/", custom_images))

    podir = os.path.join (os.path.realpath ("."), "po")
    if os.path.isdir (podir):
        buildcmd = "msgfmt -o build/locale/%s/specto.mo po/%s.po"
        mopath = "build/locale/%s/specto.mo"
        destpath = "share/locale/%s/LC_MESSAGES"
        for name in os.listdir (podir):
            if name[-2:] == "po":
                name = name[:-3]
                if sys.argv[1] == "build" \
                   or (sys.argv[1] == "install" and \
                       not os.path.exists (mopath % name)):
                    if not os.path.isdir ("build/locale/" + name):
                        os.makedirs ("build/locale/" + name)
                    os.system (buildcmd % (name, name))
                data_files.append ((destpath % name, [mopath % name]))

    if sys.argv[1] == "install":
        gtk_update_icon_cache = "gtk-update-icon-cache -f -t \
    %s/share/icons/hicolor" % prefix
        root_specified = len (filter (lambda s: s.startswith ("--root"),
                                      sys.argv)) > 0
        if not root_specified:
            print "Updating Gtk icon cache."
            os.system (gtk_update_icon_cache)
        else:
            print '''*** Icon cache not updated. After install, run this:
    ***     %s''' % gtk_update_icon_cache

if sys.argv[1] == "clean":
    try:
        os.remove ("data/indicator/specto")
        os.remove ("specto.desktop")
    except:
        pass


setup(name = "specto",
    version = version,
    description = "A desktop application that will watch configurable events (website updates, emails, file and folder changes...)",
    author = "Jean-Francois Fortin Tam",
    author_email = "nekohayo at gmail dot com",
    url = "http://specto.sourceforge.net",
    packages = [('spectlib'), ('spectlib/plugins'), ('spectlib/tools')],
    scripts = ['specto'],
    data_files = data_files,
    cmdclass = {"uninstall" : uninstall,
                "install" : install,
                "install_data" : install_data}
    )
