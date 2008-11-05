# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       about.py
#
# See the AUTHORS file for copyright ownership information

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

import sys
import os
import pygtk
pygtk.require("2.0")
import gtk
import spectlib.util
from spectlib.i18n import _

class About:
    """
    Class to create a window with the credits and licensing information about Specto.
    """
    
    def __init__(self, specto):
        self.specto = specto
        version_file_path = (spectlib.util.get_path(category="doc") + 'VERSION')
        version_file=open(version_file_path, 'r')
        version = str(version_file.readline()[:-1]) # "[:-1]" means we omit the last character, which is "\n".
        version_file.close
        license_file_path = (spectlib.util.get_path(category="doc") + 'COPYING')
        license_file = open(license_file_path, "r")
        license = license_file.read()
        license_file.close()
        license = str(license)
        authors = ["Jean-Francois 'Kiddo' Fortin Tam\n\t<nekohayo AT gmail DOT com>\n", 
                    "Pascal Potvin\n\t<pascal.potvin AT gmail DOT com>\n",
                    "Wout Clymans\n\t<woutclymans AT gmail DOT com>\n",
                    "Giulio 'Dullboy' lotti\n\t<dullgiulio AT gmail DOT com>\n",
                    "Thomas McColgan\n\t<thomas DOT mccolgan AT gmx DOT de>\n",
                    "Conor 'majikstreet' Callahan\n\t<majikstreet AT gmail DOT com>\n",
                    "Chris 'RAOF' Halse Rogers\n\t<chalserogers AT gmail DOT com>\n"
                   ]
        logo = gtk.gdk.pixbuf_new_from_file(self.specto.PATH + 'icons/specto_about.png' )

        translator_credits = _("translator-credits-your-names-go-here")

        #create tree
        self.about=gtk.AboutDialog()

        self.about.set_name("Specto")
        self.about.set_version(version)
        self.about.set_copyright("Jean-Francois Fortin Tam")
        #self.wTree.set_comments(comments)
        self.about.set_license(license)
        #self.wTree.set_wrap_license(license)
        gtk.about_dialog_set_url_hook(lambda about, url: self.url_show(url))
        self.about.set_website("http://specto.sourceforge.net")
        self.about.set_website_label(_("Specto's Website"))
        self.about.set_authors(authors)
        #self.about.set_documenters(documenters)
        #self.about.set_artists(artists)
        self.about.set_translator_credits(translator_credits)
        self.about.set_logo(logo)
        
        icon = gtk.gdk.pixbuf_new_from_file(self.specto.PATH + 'icons/specto_window_icon.png' )
        self.about.set_icon(icon)
        #self.wTree.set_logo_icon_name(icon_name)
                
        self.about.connect("response", lambda d, r: self.close())
        
        self.about.show_all()
        
    def url_show(self, url):
        os.system(spectlib.util.return_webpage(url) + " &")

    def close(self):
        self.about.destroy()

if __name__ == "__main__":
    #run the gui
    app=About()
    gtk.main()
