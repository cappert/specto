# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       watch_mail_gwave.py
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
import re
import json
import urllib2
import cookielib
import os
from urllib import urlencode

from spectlib.watch import Watch
import spectlib.config
import spectlib.gtkconfig
from spectlib.i18n import _
import spectlib.util

type = "Watch_mail_gwave"
type_desc = _("Google Wave")
icon = 'googlewave'
category = _("Mail")


def get_add_gui_info():
    return [("username", spectlib.gtkconfig.Entry(_("Username"))),
            ("password", spectlib.gtkconfig.PasswordEntry(_("Password")))]


class Watch_mail_gwave(Watch):
    """
    this watch will check if you have a new mail on your google wave account
    """

    def __init__(self, specto, id, values):
        watch_values = [("username", spectlib.config.String(True)),
                        ("password", spectlib.config.String(True))]
        url = "https://wave.google.com"
        self.standard_open_command = spectlib.util.return_webpage(url)

        #Init the superclass and set some specto values
        Watch.__init__(self, specto, id, values, watch_values)

        self.use_network = True
        self.icon = icon
        self.type_desc = type_desc
        self.cache_file = os.path.join(self.specto.CACHE_DIR, "gwave" + self.username + ".cache")

        #watch specific values
        self.newMsg = 0
        self.waves = Wave_collection()

        self.read_cache_file()

    def check(self):
        """ Check for new mails on your gmail account. """
        try:
            if "@" not in self.username:
                self.username += "@gmail.com"
            wave = Gwave()
            wave.login(self.username, self.password)
            data = wave.get_unread_waves()
            self.newMsg = 0
            
            for wave in data:
                if "unread" in wave and "title" in wave:
                    self.newMsg += int(wave['unread'])
                    wave_ = Gwave_(wave['title'], int(wave['unread']))
                    if self.waves.add(wave_):
                        self.actually_changed = True
                
            self.write_cache_file()
        except urllib2.URLError, e:
            self.set_error(str(e))  # This '%s' string here has nothing to translate
        except:
            self.set_error()
        Watch.timer_update(self)

    def get_gui_info(self):
        return [(_("Name"), self.name),
                (_("Last changed"), self.last_changed),
                (_("Username"), self.username),
                (_("Unread waves"), self.newMsg)]

    def get_balloon_text(self):
        """ create the text for the balloon """
        if self.newMsg == 1:
            text = _("Unread wave in %s") % self.waves[0].title
        else:
            i = 0 #show max 4 mails
            author_info = ""
            while i < self.newMsg and i < 4:
                author_info += self.waves[i].title + ", "
                if i == 3 and i < self.newMsg - 1:
                    author_info += "and others..."
                i += 1
            author_info = author_info.rstrip(", ")
            text = _("%d new waves in <b>%s</b>.") % (self.newMsg, author_info)
        return text

    def get_extra_information(self):
        i = 0
        author_info = ""
        while i < self.newMsg and i < 4:
            author_info += "<b>" + self.waves[i].title + "</b>: <i>" + str(self.waves[i].unread) + "</i>\n"
            if i == 3 and i < self.newMsg - 1:
                author_info += _("and others...")
            i += 1
        return author_info

    def read_cache_file(self):
        if os.path.exists(self.cache_file):
            try:
                f = open(self.cache_file, "r")
            except:
                self.specto.logger.log(_("There was an error opening the file %s") % self.cache_file, "critical", self.name)
            else:
                for line in f:
                    info = line.split("&Separator;")
                    wave_ = Gwave_(info[0], int(info[1]))
                    self.waves.add(wave_)
            finally:
                f.close()

    def write_cache_file(self):
        try:
            f = open(self.cache_file, "w")
        except:
            self.specto.logger.log(_("There was an error opening the file %s") % self.cache_file, "critical", self.name)
        else:
            for wave_ in self.waves:
                f.write(wave_.title + "&Separator;" + str(wave_.unread) + "\n")

        finally:
            f.close()

    def remove_cache_files(self):
        os.unlink(self.cache_file)
        
class Gwave_:
    def __init__(self, title, unread):
        self.title = title
        self.unread = unread 
        
class Wave_collection():

    def __init__(self):
        self.wave_collection = []

    def add(self, wave):
        self.new = True
        for _wave in self.wave_collection:
            if wave.title == _wave.title and wave.unread <= _wave.unread:
                self.new = False
                _wave.found = True

        if self.new == True:
            wave.found = True
            wave.new = True
            self.wave_collection.append(wave)
            return True
        else:
            return False

    def __getitem__(self, id):
        return self.wave_collection[id]

    def __len__(self):
        return len(self.wave_collection)

    def remove_old(self):
        i = 0
        collection_copy = []
        for _wave in self.wave_collection:
            if _wave.found == True:
                collection_copy.append(_wave)
            i += 1
        self.wave_collection = collection_copy

    def clear_old(self):
        for _wave in self.wave_collection:
            _wave.found = False
            _wave.new = False

    def get_unread_messages(self):
        unread = []
        for _wave in self.wave_collection:
            if _wave.new == True:
                unread.append(_wave)
        return unread               

class Gwave:
    def __init__(self):
        cj = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        self.authdata = {}

    def login(self, email, password):
        url = 'https://www.google.com/accounts/ClientLogin'
        header = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'accountType': 'GOOGLE',
            'Email': email,
            'Passwd': password,
            'service': 'wave',
            'source': 'specto',
        }
        request = urllib2.Request(url, urlencode(data), header)
        response = urllib2.urlopen( request )  
        body = response.read()
        
        if body.startswith('Error=BadAuthentication'):
            raise Exception("Error logging in")
    
        for line in body.split('\n'):
            if not line: continue
            key, value = line.split('=')
            self.authdata[key] = value
        
    def _get_inbox(self):
        url = 'https://wave.google.com/wave/?nouacheck&auth=' + self.authdata['Auth']
        headers = {
            'User-Agent': 'python-wave-surfer'
        }
        body = self.opener.open(urllib2.Request(url, headers=headers)).read()
        p = re.compile('var json = (\{\s?"r"\s?:\s?"\^d1".*\});')
        data = p.search(body).groups()[0]
        return json.loads(data)
    
    def _parse_inbox(self, jsondata):
        l = jsondata['p']['1']
        result = []
        for e in l:
            d = {}
            d['url'] = e['1']
            d['title'] = e['9']['1']
            d['unread'] = int(e['7'])
            d['total'] = int(e['6'])
            result.append(d)
        return result
    
    def get_waves(self):
        """Return a list with all the waves.
        The elements of the list are dicts with the following keys:
        url, title, unread, total"""
        jsondata = self._get_inbox()
        waves = self._parse_inbox(jsondata)
        return waves
    
    def get_unread_waves(self):
        """Return the list of unread waves."""
        waves = filter(lambda x: x['unread'] > 0, self.get_waves())
        return waves       
