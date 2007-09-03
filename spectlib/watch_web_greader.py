# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       watch_web_greader.py
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

from spectlib.watch import Watch
from spectlib.i18n import _

import urllib
import urllib2
import re
import sys,os, string
from xml.dom import minidom, Node

import thread
import gtk, time


class Google_reader(Watch):
    """
    this watch will check if you have a new mail on your gmail account
    """
    updated = False
    actually_updated = False
    type = 5 
    
    
##    subscription_list_url = reader_url + '/api/0/subscription/list'
##    reading_url = reader_url + '/atom/user/-/state/com.google/reading-list'
##    read_items_url = reader_url + '/atom/user/-/state/com.google/read'
##    reading_tag_url = reader_url + '/atom/user/-/label/%s'
##    starred_url = reader_url + '/atom/user/-/state/com.google/starred'
##    subscription_url = reader_url + '/api/0/subscription/edit'
##    get_feed_url = reader_url + '/atom/feed/'

    
    def __init__(self, refresh, username, password, specto, id,  name = _("Unknown Google Reader Watch")):
        Watch.__init__(self, specto)
        self.name = name
        self.refresh = refresh
        self.user = username
        self.password = password
        self.id = id
        self.error = False
        self.news_titles = []
        self.oldMsg = 0
        self.newMsg = 0
        self.source = "Specto"
        self.google_url = 'http://www.google.com'
        self.reader_url = self.google_url + '/reader'
        self.reading_url = self.reader_url + '/atom/user/-/state/com.google/reading-list'
        self.login_url = 'https://www.google.com/accounts/ClientLogin'
        self.token_url = self.reader_url + '/api/0/token'
        
        cacheSubDir__ = os.environ['HOME'] + "/.specto/cache/"
        if not os.path.exists(cacheSubDir__):
            os.mkdir(cacheSubDir__)
        self.cache_file = cacheSubDir__ + "googleReader.xml.cache"
                
    def dict_values(self):
        return { 'name': self.name, 'refresh': self.refresh, 'username': self.user, 'password':self.password, 'type':5 }
        
    def start_watch(self):
        """ Start the watch. """
        self.thread_update()
        
    def _real_update(self):
        lock = thread.allocate_lock()
        lock.acquire()
        t=thread.start_new_thread(self.update,(lock,))
        while lock.locked():
            while gtk.events_pending():
                gtk.main_iteration()
            time.sleep(0.05)
        while gtk.events_pending():
            gtk.main_iteration()
        
    def thread_update(self):
        if not self.specto.connection_manager.connected():
            self.specto.logger.log(_("No network connection detected"),
                                   "info", self.__class__)
            self.specto.connection_manager.add_callback(self._real_update)
            self.specto.mark_watch_busy(False, self.id)
        else :
            self._real_update()
        
    def update(self, lock):
        """ Check for new mails on your gmail account. """
        self.error = False
        self.specto.mark_watch_busy(True, self.id)
        self.specto.logger.log(_("Updating watch: \"%s\"") % self.name, "info", self.__class__)
        
        try:
            self.oldMsg = self.newMsg
            self.newMsg = 0
            SID = self.get_SID()
            f = file(self.cache_file , "w")
            f.write(str(self.get_reading_list(SID)))
            f.close()
            doc = minidom.parse(self.cache_file)
            rootNode = doc.documentElement
            attributes =[] 
            self.walk(rootNode, False, attributes)
            
            if self.oldMsg == 0 and self.newMsg == 0:#no unread messages, we need to clear the watch
                self.actually_updated=False
                self.specto.notifier.clear_watch("", self.id)
            if self.newMsg > 0:
                self.actually_updated=True
                if self.oldMsg == 0:
                    self.oldMsg = self.newMsg
        except:
            self.error = True
            self.specto.logger.log(_("Watch: \"%s\" has error: Error in processing cache file") % self.name, "error", self.__class__)
            
        self.specto.mark_watch_busy(False, self.id)
        Watch.update(self, lock)
        
    #login / get SED
    def get_SID(self):
        header = {'User-agent' : self.source}
        post_data = urllib.urlencode({ 'Email': self.user, 'Passwd': self.password, 'service': 'reader', 'source': self.source, 'continue': self.google_url, })
        request = urllib2.Request(self.login_url, post_data, header)
        
        try :
            f = urllib2.urlopen( request )
            result = f.read()
        
        except:
            self.specto.logger.log(_("Watch: \"%s\" has error: wrong username/password") % self.name, "error", self.__class__)
            
        return re.search('SID=(\S*)', result).group(1)
    
    def walk(self, parent, get_news, attributes):                              # [1]
        for node in parent.childNodes:
            if node.nodeType == Node.ELEMENT_NODE:
                attrs = node.attributes
                for attrName in attrs.keys():
                    attrNode = attrs.get(attrName)
                    attrValue = attrNode.nodeValue
                    if node.nodeName == "entry":
                        attributes.append(attrName)
                        get_news = True
                        
                    if node.nodeName == 'title' and get_news == True:
                        self.get_news_information(node, attrs, attrName)
                        get_news = False
                if 'gr:is-read-state-locked' in attributes:
                    get_news = False
                # Walk the child nodes.
                self.walk(node, get_news, attributes)
            
    def get_news_information(self,node, attrs, attrName):
        # Walk over any text nodes in the current node.
        content = []
        for child in node.childNodes:
            if child.nodeType == Node.TEXT_NODE:
                content.append(child.nodeValue)
                if content:
                    if content[0] not in self.news_titles:
                        #print content[0] #uncomment this to see the titles from the unread news items
                        self.news_titles.append(content[0])
                        self.newMsg +=1
    
    #get a feed of the users unread items    
    def get_reading_list(self,SID):
        return self.get_results(SID, self.reading_url)
    
    #get results from url
    def get_results(self, SID, url):
        header = {'User-agent' : self.source}
        header['Cookie']='Name=SID;SID=%s;Domain=.google.com;Path=/;Expires=160000000000' % SID

        request = urllib2.Request(url, None, header)
        
        try :
            f = urllib2.urlopen( request )
            result = f.read()
        
        except:
            self.specto.logger.log(_("Watch: \"%s\" has error: Error getting data from %s") % self.name %url, "error", self.__class__)
        
        return result
        
    def set_username(self, username):
        """ Set the username for the watch. """
        self.user = username
        
    def set_password(self, password):
        """ Set the password for the watch. """
        self.password = password
