# -*- coding: utf-8 -*-

# Specto , Unobtrusive event notifier
#
#       watch_music_lastfm.py
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

from spectlib.watch import Watch
import spectlib.config
import spectlib.gtkconfig

from urllib import urlopen
from xml.dom import minidom

type = "Watch_music_lastfm"
type_desc = _("Last.fm")
icon = 'lastfm'
category = _("Music")


def get_add_gui_info():
    return [("username", spectlib.gtkconfig.Entry(_("Username")))]

class Watch_music_lastfm(Watch):
    """
    this watch will check if a new file is played on last.fm
    """

    def __init__(self, specto, id, values):
        watch_values = [("username", spectlib.config.String(True))]
        self.standard_open_command = ""     

        #Init the superclass and set some specto values
        Watch.__init__(self, specto, id, values, watch_values)

        self.use_network = True
        self.icon = icon
        self.type_desc = type_desc
        self.extra_information = ""
        self.previous_song = ""

    def check(self):
        """ Check if a new song is played on last.fm. """
        try:
            self.lastfm_ = LastFM(self.username)
            song = self.lastfm_.updateData()
            if song != self.previous_song:
                self.previous_song = song
                self.actually_changed = True
        except:
            self.set_error()
        Watch.timer_update(self)

    def get_gui_info(self):
        return [(_("Name"), self.name),
                (_("Last changed"), self.last_changed),
                (_("Username"), self.username),
                (_("Last song"), self.previous_song)]

    def get_balloon_text(self):
        """ create the text for the balloon """
        return self.previous_song

    def get_extra_information(self):
        self.extra_information = self.previous_song + "\n" + self.extra_information
        return self.extra_information
        
class LastFM:
    # Delay in seconds after which the last song entry is considered too old tox
    # be displayed.
    MAX_DELAY = 600
    
    ARTIST = 0
    NAME = 1
    ALBUM = 2
    TIME = 3
    
    def __init__(self, username, proxies=None):
        """
        Create a new LastFM object.
        
        username, the Last.fm username
        proxies, the list of proxies to use to connect to the Last.fm data, as
        expected by urllib.urlopen()
        """
        self.lastfm_url = 'http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=%s&limit=1&api_key=b25b959554ed76058ac220b7b2e0a026'                
        self.setUsername(username)
        self._proxies = proxies
        self.scrobbling = False
    
    def getUsername(self):
        return self._username
    
    def setUsername(self, username):
        self._username = username
        self.lastSong = ""
    
    def updateData(self):
        """
        Fetch the last recent tracks list and update the object accordingly.
    
        Return True if the last played time has changed, False otherwise.
        """
        # Where to fetch the played song information
        try:
            xmldocument = urlopen(self.lastfm_url % self._username, self._proxies)
            xmltree = minidom.parse(xmldocument)
        except Exception:
            raise Exception('XML document not formed as expected')
    
        if xmltree.childNodes.length != 1:
            raise Exception('XML document not formed as expected')
    
        recenttracks = xmltree.childNodes[0]
    
        tracklist = recenttracks.getElementsByTagName('track')
        
    
        # do not update if nothing more has been scrobbled since last time
        if tracklist[0].getAttribute('nowplaying') == 'true':
            track = tracklist[0]
            artistNode = track.getElementsByTagName('artist')[0]
            if artistNode.firstChild:
                artist = artistNode.firstChild.data
            else:
                artist = ""
    
            nameNode = track.getElementsByTagName('name')[0]
            if nameNode.firstChild:
                name = nameNode.firstChild.data
            else:
                name = ""
            
            albumNode = track.getElementsByTagName('album')[0]
            if albumNode.firstChild:
                album = albumNode.firstChild.data
            else:
                album = "" 
            
            self.lastSong = _(artist + ": " + name + " (" + album + ")")
        return self.lastSong
    
    def getLastSong(self):
            return self.lastSong
