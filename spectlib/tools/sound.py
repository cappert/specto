# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       sound.py
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

import pygst
pygst.require("0.10")
import gst

class Sound:
    def __init__(self):
        self.player = None
        
    def play(self, uri):
        if uri:
            self.player = gst.element_factory_make("playbin", "player")
            uri =  "file://" + uri
            self.player.set_property('uri', uri)
            self.player.set_state(gst.STATE_PLAYING)