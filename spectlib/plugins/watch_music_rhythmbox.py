# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       watch_music_rhythmbox.py
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

from spectlib.watch import Watch
from spectlib.i18n import _
import dbus

type = "Watch_music_rhythmbox"
type_desc = _("Rhythmbox")
icon = 'rhythmbox'
category = _("Music")
dbus_watch = True


class Watch_music_rhythmbox(Watch):
    """
    Watch class that will check if a song has changed in rhythmbox.
    """

    def __init__(self, specto, id, values):

        watch_values = []
        self.icon = icon
        self.current_song = ""
        self.standard_open_command = 'rhythmbox'
        self.type_desc = type_desc

        #Init the superclass and set some specto values
        Watch.__init__(self, specto, id, values, watch_values)
        
        self.dbus = True
        self.message = ""
        self.extra_info = ""
        # Use the dbus interface we saw in dbus-notify
        self.dbus_interface = "org.gnome.Rhythmbox.Player"
        self.dbus_path = "/org/gnome/Rhythmbox/Player"
        self.dbus_name = "org.gnome.Rhythmbox"

        self.signals = {"playingUriChanged": self.playingUriChanged}
        
        
    def playingUriChanged(self, uri):
        metadata = {}
        info = ["artist", "album", "title", "track-number"]

        shell = self.get_rhythmbox_interface()
        if uri:
            data = shell.getSongProperties(uri)
            for key in data:
                if key in info:
                    metadata[key] = data[key]

            header = metadata["title"]
            self.message = "%s - %s\nTrack: %d" %(metadata["artist"],metadata["title"],metadata["track-number"])
            self.current_song = "%s - %s" % (metadata["artist"], metadata["title"])
            self.watch_changed()
    
    def get_balloon_text(self):
        """ create the text for the balloon """
        return self.message

    def get_gui_info(self):
        return [(_('Name'), self.name),
                (_('Last changed'), self.last_changed),
                (_('Current track'), self.current_song)]
                
    def get_rhythmbox_interface(self):
        rhythmbox_object = self.session_bus.get_object("org.gnome.Rhythmbox", "/org/gnome/Rhythmbox/Shell")
        return dbus.Interface(rhythmbox_object, "org.gnome.Rhythmbox.Shell")                
