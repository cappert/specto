# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       util.py
#
# Copyright (c) 2005-2007, Jean-François Fortin Tam

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import os, sys
from spectlib.specto_gconf import Specto_gconf
import gnomevfs

def show_webpage(webpage):
    """ Open the webpage in the default browser. """
    specto_gconf = Specto_gconf("/desktop/gnome/url-handlers/http")
    default_browser = specto_gconf.get_entry("command")
    clean_url = str(webpage.replace("&", "\&"))
    os.system((default_browser % clean_url) + " &") #open the browser with the page

def open_gconf_application(key):
    """ Get the name from gconf and open the application. """
    specto_gconf = Specto_gconf(key)
    application = specto_gconf.get_entry("command")
    if "mailto" in key:
        application = application.replace(" %s", "")#this is an ugly hack, because evolution really doesn't want to startup with %s
    os.system(application + " &")
    
def open_file_watch(f):
    """ Open a file with the correct application (mime). """
    mime_type = gnomevfs.get_mime_type(f)
    application = gnomevfs.mime_get_default_application(mime_type)
    os.system(application[2] + " \"" + f + "\" &")

def get_path(category=None):
    """ Return the correct path. """
    if not os.path.exists('data'):
        if not category:
            PATH = "%s/share/specto/" % sys.prefix
        elif category=="doc":
            PATH = "%s/share/doc/specto/" % sys.prefix
    else:
        if not category:
            PATH =os.path.join(os.getcwd(), "data/")
        elif category=="doc":
            PATH = os.path.join(os.getcwd(), "data/doc/")
    return PATH

