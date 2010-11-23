# -*- coding: utf-8 -*-

# Specto , Unobtrusive event notifier
#
#       watch_web_greader.py
#
# See the AUTHORS file for copyright ownership information

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or(at your option) any later version.
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
import spectlib.util

import urllib2
import urllib 
import re
import os
from xml.dom import minidom
from xml.etree import ElementTree as ET

type = "Watch_web_greader"
type_desc = _("Google Reader")
icon = 'internet-news-reader'
category = _("Internet")


def get_add_gui_info():
    return [("username", spectlib.gtkconfig.Entry(_("Username"))),
           ("password", spectlib.gtkconfig.PasswordEntry(_("Password")))]


class Watch_web_greader(Watch):
    """
    this watch will check if you have new news on your google reader account
    """

    def __init__(self, specto, id, values):
        watch_values = [("username", spectlib.config.String(True)),
                      ("password", spectlib.config.String(True))]

        url = "http://www.google.com/reader/"
        self.standard_open_command = spectlib.util.return_webpage(url)

        #Init the superclass and set some specto values
        Watch.__init__(self, specto, id, values, watch_values)

        self.use_network = True
        self.icon = icon
        self.type_desc = type_desc
        self.cache_file = os.path.join(self.specto.CACHE_DIR, "greader" + self.username + ".cache")

        #watch specific values
        self.unreadMsg = 0
        self.newMsg = 0
        self.news_info = Feed_collection()
        self.or_more = ""

        self.read_cache_file()

    def check(self):
        """ Check for new news on your greader account. """
        try:
            self.newMsg = 0
            self.unreadMsg = 0
            greader = Greader(self.username, self.password, "specto")
            auth = greader.login()
            feed_db = greader.get_unread_items(auth)
            for feed in feed_db:
                self.unreadMsg += feed.messages
                if feed.messages > 0 and self.news_info.add(feed):
                    self.actually_changed = True
                    self.newMsg += feed.messages
            if self.unreadMsg == 0:#no unread items, we need to clear the watch
                self.mark_as_read()
                self.news_info = Feed_collection()
            else:
                if self.unreadMsg == 1000:
                    self.or_more = _(" or more")
                
            self.write_cache_file()

        except:
            self.set_error()

        Watch.timer_update(self)

    def get_gui_info(self):
        return [(_('Name'), self.name),
               (_('Last changed'), self.last_changed),
               (_('Username'), self.username),
               (_('Unread messages'), str(self.unreadMsg) + self.or_more)]

    def get_balloon_text(self):
        """ create the text for the balloon """
        unread_messages = self.news_info.get_unread_messages()
        if len(unread_messages) == 1:
            text = _("New newsitems in <b>%s</b>...\n\n... <b>totalling %s</b> unread items.") %(unread_messages[0].name, str(self.unreadMsg) + self.or_more)
        else:
            i = 0 #show max 4 feeds
            feed_info = ""
            while i < len(unread_messages) and i < 4:
                feed_info += unread_messages[i].name + ", "
                if i == 3 and i < len(unread_messages) - 1:
                    feed_info += _("and others...")
                i += 1
            feed_info = feed_info.rstrip(", ")
            text = _("%d new newsitems in <b>%s</b>...\n\n... <b>totalling %s</b> unread items.") %(self.newMsg, feed_info, str(self.unreadMsg) + self.or_more)
        return text

    def get_extra_information(self):
        i = 0
        feed_info = ""
        while i < len(self.news_info) and i < 4:
            # TODO: do we need to self.escape the name and messages?
            feed_info += "<b>" + self.news_info[i].name + "</b>: <i>" + str(self.news_info[i].messages) + "</i>\n"
            if i == 3 and i < len(self.news_info) - 1:
                feed_info += _("and others...")
            i += 1
        return feed_info

    def read_cache_file(self):
        if os.path.exists(self.cache_file):
            try:
                f = open(self.cache_file, "r")
            except:
                self.specto.logger.log(_("There was an error opening the file %s") % self.cache_file, "critical", self.name)
            else:
                for line in f:
                    info = line.split("&Separator;")
                    feed = Feed(info[0], info[1].replace("\n", ""))
                    self.news_info.add(feed)

            finally:
                f.close()

    def write_cache_file(self):
        self.news_info.remove_old()
        try:
            f = open(self.cache_file, "w")
        except:
            self.specto.logger.log(_("There was an error opening the file %s") % self.cache_file, "critical", self.name)
        else:
            for feed in self.news_info:
                f.write(feed.name + "&Separator;" + str(feed.messages) + "\n")
        finally:
            f.close()

    def remove_cache_files(self):
        os.unlink(self.cache_file)


class Feed():

    def __init__(self, name, messages):
        self.name = name
        self.messages = int(messages)
        self.found = False
        self.new = False


class Feed_collection():

    def __init__(self):
        self.feed_collection = []

    def add(self, feed):
        self.new = True
        self.changed = False
        for _feed in self.feed_collection:
            if feed.name == _feed.name:
                if feed.messages > _feed.messages:
                    self.new = False
                    self.changed = True
                    _feed.messages = feed.messages
                    _feed.found = True
                else:
                    _feed.messages = feed.messages
                    self.new = False
                    _feed.found = True

        if self.new == True:
            feed.found = True
            feed.new = True
            self.feed_collection.append(feed)
            return True
        elif self.changed == True:
            feed.found = True
            feed.updated = True
            return True
        else:
            return False

    def __getitem__(self, id):
        return self.feed_collection[id]

    def __len__(self):
        return len(self.feed_collection)

    def remove_old(self):
        i = 0
        collection_copy = []
        for _feed in self.feed_collection:
            if _feed.found == True:
                collection_copy.append(_feed)
            i += 1
        self.feed_collection = collection_copy

    def clear_old(self):
        for _feed in self.feed_collection:
            _feed.found = False
            _feed.new = False
            _feed.updated = False

    def get_unread_messages(self):
        unread = []
        for _feed in self.feed_collection:
            if _feed.new == True or _feed.updated == True:
                unread.append(_feed)
        return unread

class Greader:
    def __init__(self, user, password, source):    
        self.google_url = 'http://www.google.com'  
        self.reader_url = self.google_url + '/reader'  
        self.login_url = 'https://www.google.com/accounts/ClientLogin'  
        self.read_items_url = self.reader_url + '/api/0/unread-count'
        self.list_feeds_url = self.reader_url + '/api/0/subscription/list'
        self.source = source
        self.user = user
        self.password = password
    
    def login(self):
        #login / get SED    
        header = {'User-agent' : self.source}  
        post_data = urllib.urlencode({ 'Email': self.user, 'Passwd': self.password, 'service': 'reader', 'source': self.source, 'continue': self.google_url, })  
        request = urllib2.Request(self.login_url, post_data, header)  
          
        try :  
            f = urllib2.urlopen( request )  
            result = f.read()  
          
        except:  
            raise Exception('Error logging in')
              
        return re.search('Auth=(\S*)', result).group(1)  
  
    def get_results(self, auth, url):
        #get results from url  
        header = {'User-agent' : self.source}  
        header['Authorization']='GoogleLogin auth=%s' % auth  
      
        request = urllib2.Request(url, None, header)  
          
        try :  
            f = urllib2.urlopen( request )  
            result = f.read()  
          
        except:  
            raise Exception('Error getting data from %s' % url)  
          
        return result  
  
    #get a feed of the users read items      
    def get_unread_items(self, auth):
        feed_db = []  
        data = self.get_results(auth, self.read_items_url)
        feed_data = self.list_feeds(auth)
        node = ET.XML(data)
        feed_node = ET.XML(feed_data)
        
        total_unread = 0
        node = node.find("list")
        feed_node = feed_node.find("list")
        for o in node.findall("object"):
            feed = ""
            total_unread = 0
            feed_title = ""
            for n in o.findall("string"):
                if (n.attrib["name"] == "id"):
                    feed = n.text
            for n in o.findall("number"):
                if (n.attrib["name"] == "count"):
                    total_unread = int(n.text)
            if feed[0:5] != "user/":
                for x in feed_node.findall("object"):
                    found = False
                    for y in x.findall("string"):
                        if(y.attrib["name"] == "id" and y.text == feed):
                            found = True
                        if(y.attrib["name"] == "title" and found == True):
                            feed_title = y.text
                if feed_title != "" and total_unread > 0:
                    f = Feed(feed_title, total_unread)
                    feed_db.append(f)
        return feed_db
    
    def list_feeds(self, auth):
        return self.get_results(auth, self.list_feeds_url)
