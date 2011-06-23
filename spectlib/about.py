# -*- coding: utf-8 -*-

# Specto , Unobtrusive event notifier
#
#       about.py
#
# See the AUTHORS file for copyright ownership information

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
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

import os
import pygtk
pygtk.require("2.0")
import gtk

from spectlib.util import show_webpage, get_path


class About:
    """
    Class to create a window with the credits
    and licensing information about Specto.
    """

    def __init__(self, specto):
        self.specto = specto

        license_file_path = (os.path.join(get_path(category="doc"), "COPYING"))
        with open(license_file_path, "r") as license_file:
            license = license_file.read()

        authors_file_path = (os.path.join(get_path(category="doc"), "AUTHORS"))
        with open(authors_file_path, "r") as authors_file:
            # this is a hack, because gtk.AboutDialog expects a list, not a file
            authors = authors_file.readlines()

        logo = gtk.gdk.pixbuf_new_from_file(os.path.join(self.specto.PATH, "icons/specto_about.png"))

        # gtk.AboutDialog will detect if "translator-credits" is untranslated,
        # and hide the tab.
        translator_credits = _("translator-credits")

        #create tree
        self.about = gtk.AboutDialog()

        self.about.set_name("Specto")
        self.about.set_version(self.specto.VERSION)
        self.about.set_copyright("Copyright © Jean-François Fortin Tam & Wout Clymans")
        self.about.set_comments(_("Be notified of everything"))
        self.about.set_license(license)
        #self.wTree.set_wrap_license(license)
        gtk.about_dialog_set_url_hook(lambda about, url: show_webpage(url))
        self.about.set_website("http://specto.sourceforge.net")
        self.about.set_website_label(_("Specto's Website"))
        self.about.set_authors(authors)
        #self.about.set_documenters(documenters)
        #self.about.set_artists(artists)
        self.about.set_translator_credits(translator_credits)
        self.about.set_logo(logo)

        self.about.set_icon_from_file(self.specto.LOGO_PATH)

        self.about.connect("response", lambda d, r: self.close())

        self.about.show_all()

    def close(self):
        self.about.destroy()


if __name__ == "__main__":
    #run the gui
    app = About()
    gtk.main()
