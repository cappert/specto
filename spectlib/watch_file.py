#!/usr/bin/env python
# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       watch_file.py
#
# Copyright (c) 2005-2007, Jean-François Fortin Tam
# This module code is maintained by : Jean-François Fortin, Pascal Potvin and Wout Clymans

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

import os, re
from stat import *
from spectlib.i18n import _
import thread
import gtk, time

cacheSubDir__ = os.environ['HOME'] + "/.specto/cache/"
if not os.path.exists(cacheSubDir__):
    os.mkdir(cacheSubDir__)
    
class File_watch(Watch):
    """ 
    Watch class that will check if a file was modified, removed or created. 
    """
    updated = False
    type = 2
    
    def __init__(self, refresh, file, mode, specto, id,  name = _("Unknown File Watch")):
        Watch.__init__(self, specto)
        self.name = name
        self.refresh = refresh
        self.file = file
        self.mode = mode
        self.id = id
        self.error = False
        self.first_time = False

    def dict_values(self):
        return { 'name': self.name, 'refresh': self.refresh, 'file': self.file, 'mode':self.mode, 'type':2 }
       
    def start_watch(self):
        """ Start the watch. """
        self.thread_update()
        
    def thread_update(self):
        lock = thread.allocate_lock()
        lock.acquire()
        t=thread.start_new_thread(self.update,(lock,))
        while lock.locked():
            while gtk.events_pending():
                gtk.main_iteration()
            time.sleep(0.05)
        while gtk.events_pending():
            gtk.main_iteration()  
                
    def update(self, lock):
        """ See if a file was modified or created. """
        self.error = False
        self.specto.mark_watch_busy(True, self.id)
        self.specto.logger.log(_("Updating watch: \"%s\"") % self.name, "info", self.__class__)
        
        try:
            self.get_cache_file()
            self.old_values = self.read_options()
            mode = os.stat(self.file)[ST_MODE]
            self.new_files = []
            if S_ISDIR(mode):
                self.get_dir(self.file)
                self.write_options()#write the new values to the cache file
                self.old_values = self.read_options() #read the new valeus
                self.get_removed_files() #remove the files that were removed
                self.write_options()#write the values (with the removed lines) to the cache file
            else:
                self.get_file(self.file)
                self.write_options()
                
            #first time don't mark as updated
            if self.first_time == True:
                self.updated = False
                self.first_time = False            
        except:
            self.error = True
            self.specto.logger.log(_("Watch: \"%s\" has an error") % self.name, "error", self.__class__)
        
        self.specto.mark_watch_busy(False, self.id)
        lock.release()
        Watch.update(self)
                
    def get_file(self, file_):
        """ Get the info from a file and compair it with the previous info. """
        size = int(os.stat(file_)[6]) #mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime = info
        old_size = re.search('%s:\s(.+)' % file_, self.old_values)
        if old_size and size: 
            old_size = int(old_size.group(1))
            if size != old_size:
                #replace filesize
                self.old_values = self.old_values.replace(file_ + ": " + str(old_size), file_ + ": " + str(size))
                print _("update: %s was modified") % file_
                self.updated = True
        elif (size or size ==0) and not old_size:
            #add the file to the list
            self.old_values += file_ + ": " + str(size) + "\n"
            print _("update: %s was created") % file_
            self.updated = True
            
    def get_dir(self, dir_):
        """ Recursively walk a directory. """
        for f in os.listdir(dir_):
            pathname = os.path.join(dir_, f)
            mode = os.stat(pathname)[ST_MODE]
            if S_ISDIR(mode): # It's a directory, recurse into it
                self.get_dir(pathname)
            elif S_ISREG(mode): # It's a file, get the info
                self.new_files.append(pathname)
                self.get_file(pathname)
            else: # Unknown file type, print a message
                print _('Skipping %s' % pathname)
                
    def get_removed_files(self):
        """ Get the removed files. """
        old_values_ = self.old_values.split("\n")
        self.old_values = ""
        y = 0
        for i in self.old_files:
            if i not in self.new_files:#see if a old file still exists in the new files list
                print _("update: %s removed") % i
                self.updated = True
            else:
                self.old_values += old_values_[y] + "\n"
            y+=1
        
    def write_options(self):
        """ Write the new values in the cache file. """
        f = file(self.file_name, "w")
        f.write(str(self.old_values))
        f.close()
        
    def read_options(self):
        """ Read the options from the cache file. """
        try:
            f = file(self.file_name, "r")# Load up the cached version
            text = ""
            self.old_files = []
            for line in f:
                self.old_files.append(line.split(':')[0])
                text += line
            f.close()
            return text
        except:
            pass

    def get_cache_file(self):
        """ Create and open the cache file. """
        self.file_name = cacheSubDir__ + self.file.replace("/","_") + ".cache"
        if not os.path.exists(self.file_name):
            f = open(self.file_name, "w")
            f.close()
            self.first_time = True
        os.chmod(self.file_name, 0600) 
    
    def set_file(self, file):
        """ Set the filename. """
        self.file = file
