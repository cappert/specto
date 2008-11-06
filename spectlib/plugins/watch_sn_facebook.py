# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       watch_sn_facebook.py
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
import spectlib.config
import spectlib.gtkconfig
from spectlib.i18n import _
import sys, os

import formatter
import htmllib
import urllib2
import re
from cStringIO import StringIO

type = "Watch_sn_facebook"
type_desc = _("Facebook")
icon = 'facebook'
category = _("Social networks")

def get_add_gui_info():
    return [
            ("email", spectlib.gtkconfig.Entry(_("Email"))),
            ("password", spectlib.gtkconfig.PasswordEntry(_("Password")))
            ]
           
class Watch_sn_facebook(Watch):
    """ 
    Watch class that will check if a bzr folder has been changed. 
    """
    
    def __init__(self, specto, id, values):
        
        watch_values = [ 
                        ( "email", spectlib.config.String(True) ),
                        ( "password", spectlib.config.String(True) )
                       ]
        
        self.icon = icon
        self.standard_open_command = ''
        self.type_desc = type_desc 
        
        url = "http://www.facebook.com"
        self.standard_open_command = spectlib.util.return_webpage(url)         
                
        #Init the superclass and set some specto values
        Watch.__init__(self, specto, id, values, watch_values)
        
        if self.open_command == self.standard_open_command: #check if google apps url has to be used
            self.open_command = self.standard_open_command

        self.cache_file = os.path.join(self.specto.CACHE_DIR, "facebook" + self.email + ".cache")            

    def check(self):
        """ See if a folder's contents were modified or created. """        
        try:
            facebook = Facebook(self.email, self.password)
            self.messages = facebook.get_messages()
            
            for message in self.messages:
                print message.sender + ": " + message.message
                
            notifications = facebook.get_notifications()
            
            for notification in notifications:
                print notification.notification
                
            requests = facebook.get_requests()
           
            for request in requests:
                print request.request
               
            wall = facebook.get_wall()
           
            for w in wall:
                print w.poster + ": " + w.post                                        
            
            #self.write_cache_file()
        except:
            self.error = True
            self.specto.logger.log(_("Unexpected error: ") + str(sys.exc_info()[0]), "error", self.name)
        
        Watch.timer_update(self)
        
    def get_balloon_text(self):
        """ create the text for the balloon """
        msg = ""
        if len(self.local_extra) <> 0:
            if len(self.local_extra) == 1:
                msg = _("One new revision on your local branch.")
            else:
                msg = _("%d new revisions on your local branch.") % len(self.local_extra)
        if len(self.remote_extra) <> 0:
            if len(self.remote_extra) == 1:
                msg = _("One new revision on the remote branch.")
            else:
                print self.remote_extra[0]
                msg = _("%d new revisions on the remote branch.") % len(self.remote_extra)        
        return msg
        
    def get_extra_information(self):        
        i = 0
        author_info = ""
        if len(self.remote_extra) <> 0:
            while i < len(self.remote_extra) and i < 4:
                author_info += "<b>Rev " + str(self.remote_extra[i][0]) + "</b>: <i>" + str(self.remote_extra[i][1]).split("@")[0] + "</i>\n"
                if i == 3 and i < len(self.remote_extra) - 1:
                    author_info += _("and others...")
                i += 1         
        if len(self.local_extra) <> 0 and author_info == "":
            while i < len(self.local_extra) and i < 4:
                author_info += "<b>Rev " + str(self.local_extra[i][0]) + "</b>: <i>" + str(self.local_extra[i][1]).split("@")[0] + "</i>\n"
                if i == 3 and i < len(self.local_extra) - 1:
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
                    if line.startswith("local_branch:"):
                        self.local_branch_ = int(line.split(":")[1])
                    if line.startswith("remote_branch:"):
                        self.remote_branch_ = int(line.split(":")[1])
            finally:
                f.close()

        
    def write_cache_file(self):
        try:
            f = open(self.cache_file, "w")
        except:
            self.specto.logger.log(_("There was an error opening the file %s") % self.cache_file, "critical", self.name)
        else:
            f.write(self.messages)
        finally:
            f.close()
            
    def remove_cache_files(self):
        os.unlink(self.cache_file)        
        
    def get_gui_info(self):
        return [ 
                (_("Name"), self.name),
                (_("Last changed"), self.last_changed),
                (_("Email"), self.email)
                ] 
                
class Facebook():
    def __init__(self, email, password):
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        urllib2.install_opener(opener)
        urllib2.urlopen(urllib2.Request("https://login.facebook.com/login.php?m&amp;next=http%3A%2F%2Fm.facebook.com%2Fhome.php","email=%s&pass=%s&login=Login" % (email, password)))                                        
        
    def get_messages(self):
        connection = urllib2.urlopen("http://m.facebook.com/inbox/")
        messages_ = connection.read().split("<hr />")
        messages = []
        for line in messages_:
  
            #search subject
            title = re.search('<a href="/inbox/\?read=.+">(.+)</a><br /><small><a href="/profile.php', line)
            if title <> None:
                outstream = StringIO()
                p = htmllib.HTMLParser(formatter.AbstractFormatter(formatter.DumbWriter(outstream)))    
                p.feed(title.group(1))
                title = outstream.getvalue()
                outstream.close()
                
                #unread message
                unread = False
                if "&#8226;" in title:
                    title = title.replace("&#8226;", "")
                    unread = True
   
            #search sender
            sender = re.search('</a><br /><small><a href="/profile.php\?id=.+">(.+)</a><br />', line)
            if sender <> None:
                sender = sender.group(1)
  
            if sender <> None and title <> None and unread == True:  
                messages.extend([FacebookMessage(sender, title)])
                
        return messages
        
    def get_notifications(self):
        notifications = []
        connection = urllib2.urlopen("http://m.facebook.com/notifications.php")
        messages = connection.read().split("<hr />")
        for line in messages:
          
            #search notification
            notification = re.search('</b><br /><a href="/profile.php\?id=.+>(.+)<br /></div>', line)
            if notification <> None:
                outstream = StringIO()
                p = htmllib.HTMLParser(formatter.AbstractFormatter(formatter.DumbWriter(outstream)))    
                p.feed(notification.group(0))
                notification = re.sub("(\[.+\])","", outstream.getvalue())
                notification = notification.replace("\n", " ")
                outstream.close()
                notifications.extend([FacebookNotification(notification)])
        return notifications

    def get_requests(self):
        requests = []
        connection = urllib2.urlopen("http://m.facebook.com/reqs.php")
        messages = connection.read().split("<hr />")
        for line in messages:
          
            #search friend requests
            request = re.search('<a href="/profile.php\?id=.+">(.+)<div><form action=', line)
            if request <> None:
                outstream = StringIO()
                p = htmllib.HTMLParser(formatter.AbstractFormatter(formatter.DumbWriter(outstream)))
                p.feed(request.group(0))
                request = re.sub("(\[.+\])"," ", outstream.getvalue())
                p.close()
                requests.extend([FacebookRequest(request.replace("\n",""))])
        return requests
        
    def get_wall(self):
        walls = []
        connection = urllib2.urlopen("http://m.facebook.com/wall.php")
        messages = connection.read().split("<hr />")
        for line in messages:
          
            #search wall poster
            poster = re.search('<a href="/profile.php\?id=.+>(.+)<br /><small>', line)
            if poster <> None:
                outstream = StringIO()
                p = htmllib.HTMLParser(formatter.AbstractFormatter(formatter.DumbWriter(outstream)))    
                p.feed(poster.group(0))
                poster = re.sub("(\[.+\])","", outstream.getvalue())
                outstream.close()
            
            #search wall post
            post = re.search('</small></div><div>(.+)</div>', line)
            if post <> None:
                outstream = StringIO()
                p = htmllib.HTMLParser(formatter.AbstractFormatter(formatter.DumbWriter(outstream)))    
                p.feed(post.group(0))
                post = outstream.getvalue()
                outstream.close()   
        
            if poster <> None and post <> None:  
                walls.extend([FacebookWall(poster.strip(), post.strip().replace("\n",""))])
        return walls
                                                                                    

class FacebookMessage():
    def __init__(self, sender, message):
        self.sender = sender
        self.message = message
        
class FacebookNotification():
    def __init__(self, notification):
        self.notification = notification
      
class FacebookRequest():
    def __init__(self, request):
        self.request = request
        
class FacebookWall():
    def __init__(self, poster, post):
        self.poster = poster
        self.post = post                                                                