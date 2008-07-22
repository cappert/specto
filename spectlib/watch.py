# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       watch.py
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

# The Watcher : this file should give a class intended for subclassing. It should give all the basic methods.
import os, sys, time
import gobject
import gnome
import thread
import gtk

#specto imports
from spectlib.iniparser import ini_namespace
from ConfigParser import ConfigParser
from spectlib import i18n
from spectlib.i18n import _
from spectlib.balloons import NotificationToast

from time import sleep
from datetime import datetime

def gettext_noop(s):
   return s

class Watch:
    def __init__(self, specto, id, name, interval, type):
        self.name = name
        self.interval = interval
        self.type = type
        self.error = False
        self.timer_id = -1
        self.id = id
        self.updated = False
        self.specto = specto
        self.active = True #active/not active
        self.last_updated = "No updates yet"
        self.actually_updated = False
        gnome.sound_init('localhost')
        self.use_network = False
        global _
        
    def start(self):
        """ Start the watch. """
        self.active = True
        if self.use_network == True:
            self.check_connection()
        else:
            self.start_update()
            
    def stop(self):
        """ Stop the watch. """
        self.active = False
        gobject.source_remove(self.timer_id)

    def clear(self):
        """ clear the watch """
        self.updated = False

    def restart(self):
        """ restart the watch """
        if self.active == True:
            self.stop()
        self.start()        
        
    def start_update(self):
        self.specto.mark_watch_status("updating", self.id)
        self.error = False
        #self.update()
        #return
        self.lock = thread.allocate_lock()
        self.lock.acquire()
        thread.start_new_thread(self.update,())
        while self.lock.locked():
            while gtk.events_pending():
                gtk.main_iteration()
            time.sleep(0.05)
        while gtk.events_pending():
            gtk.main_iteration()
        
    def timer_update(self):
        """ update the timer """
        if self.actually_updated == True:
            self.actually_updated = False
            self.updated = True
            self.last_updated = datetime.today().strftime("%A %d %b %Y %H:%M")
            self.specto.mark_watch_status("updated", self.id)
        else:
            self.specto.mark_watch_status("idle", self.id)
        try:
            self.lock.release()
            self.timer_id = gobject.timeout_add(self.interval, self.thread_update)
        except:
            self.timer_id = gobject.timeout_add(self.interval, self.update)

    def check_connection(self):
        if not self.specto.connection_manager.connected():
            self.specto.logger.log(_("No network connection detected"),
                                   "info", self.__class__)
            self.specto.connection_manager.add_callback(self.start_update)
            self.specto.mark_watch_status("idle", self.id)
        else :
            self.start_update()

    def set_name(self, name):
        """ Set the name. """
        self.name = name

    def get_name(self):
        """ Return the name. """
        return self.name

    def set_interval(self, interval):
        self.interval = interval
        
    def get_interval(self):
        return self.interval
    
    def set_error(self, error):
        self.error = error
        
    def get_error(self):
        return self.error
    
class Watch_collection:
    def __init__(self):
        self.watch_db = []
        self.id = 0
        self.plugin_dict = {}
        self.load_plugins()
                
    def load_plugins(self):
        dir = "spectlib/plugins/"
        for f in os.listdir(dir):
            if f[-3:] == ".py":
                _file = dir + f[:-3]
                mod = __import__(_file)
                obj = sys.modules[_file]
                self.plugin_dict[obj.type] = mod        
                
    def add(self,specto, values):
        """ read the content from the dictionary and create the watch """        
        for i in values:
            type = values[i]['type']
            
            #get the right object and create the watch object
            obj = getattr(self.plugin_dict[type], type)
            watch_ = obj(specto, self.id, values[i])
            
            self.watch_db.append(watch_)
            self.id+=1
        
    def remove(self, id):
        """ remove the watch from the collection """
        self.watch_db[id].stop()
        self.watch_db[id].updated = False        
        del self.watch_db[id]
        
    def get(self, id):
        """ get a watch object """
        return self.watch_db[id]
    
    def clear_all_watches(self):
        """ mark all watches as not updated """
        for watch in self.watch_db:
            watch.clear()
        
    def start_all_watches(self):
        """ start all watches in the collection """
        for watch in self.watch_db:
            watch.start()
        
    def stop_all_watches(self):
        """ stop all watches in the collection """
        for watch in self.watch_db:
            watch.stop()
        
    def restart_all_watches(self):
        """ restart all watches in the collection """
        for watch in self.watch_db:
            if watch.activate == True:
                watch.restart()
        
    def length(self):
        """ return the length from the collection """
        return len(self.watch_db)
    
    def count_updated_watches(self):
        """ Count the number of updated watches for the tooltip. """
        count_updates = {}
        for watch in self.watch_db:
            print watch.updated
            try:
                count_updates[watch.type]
            except KeyError:
                count_updates[watch.type] = 0
            
            if watch.updated == True:
                count_updates[watch.type] += 1
                
        return count_updates
    
    def find_watch(self, name):
        """
        Returns the key of a watch or None if it doesn't exists.
        """
        k = -1
        for key in self.watch_db.iterkeys():
            if self.watch_db[key].name == name: 
                k = key
                break
        return k
    
    def check_unique_watch(self, name):
        """ Check if the watch name is unique. """
        if self.watch_io.search_watch(name) and GTK:
            return False
        else:
            return True
    
    def __getitem__(self, i):
        return self.watch_db[i]

class Watch_io:
    """
    A class for managing watches.
    """
    def __init__(self, file_name):
        #read the watch from file using the iniparser module
        self.file_name = file_name
        if not os.path.exists(self.file_name):
            try:
                f = open(self.file_name, "w")
            except:
                self.specto.logger.log(_("There was an error creating the file %s") % self.file_name, "critical", self.__class__)
            finally:
                f.close()
        os.chmod(self.file_name, 0600)#This is important for security purposes, we make the file read-write to the owner only, otherwise everyone can read passwords.
        try:
            self.cfg = ini_namespace(file(self.file_name))
        except:
            self.specto.logger.log(_("There was an error initializing config file %s") % self.file_name, "critical", self.__class__)
        
    def read_all_watches(self):
        """
        Read the watch options from the config file
        and return a dictionary containing the info needed to start the watches.
        """
        watch_value_db = {}

        try:
            self.cfg = ini_namespace(file(self.file_name))
        except:
            self.specto.logger.log(_("There was an error initializing config file %s") % self.file_name, "critical", self.__class__)
  
        names = self.cfg._sections.keys()
        i = 0
        for name_ in names:
            watch_value_db[i] = self.read_watch(name_)
            i += 1
        return watch_value_db
    
    def read_watch(self,name):
        """
        Read the watch options from one watch.
        """
        watch_options = {}
              
        try:
            self.cfg = ini_namespace(file(self.file_name))
        except:
            self.specto.logger.log(_("There was an error initializing config file %s") % self.file_name, "critical", self.__class__)
            
        options = self.cfg._sections[name]._options.keys()
        
        for option_ in options:
            watch_options_ = { option_: self.read_watch_option(name, option_) }
            watch_options.update(watch_options_) 
        watch_options.update({'name':name})
                
        return watch_options
    
    def read_watch_option(self, name, option):
        """ Read one option from a watch """
        try:
            return self.cfg[name][option]
        except:
            return 0
        
    def write_watch(self, values):
        """
        Write or change the watch options in a configuration file.
        Values has to be a dictionary with the name from the options and the value. example: { 'name':'value', 'interval':'value' }
        If the name is not found, a new watch will be added, else the excisting watch will be changed.
        """
        try:
            self.cfg = ini_namespace(file(self.file_name))
        except:
            return 0
        
        if self.cfg:
            try:
                name = values['name']

                if not self.cfg._sections.has_key(name):
                    self.cfg.new_namespace(name) #add a new watch
    
                del values['name']
                for option, value  in values.iteritems():
                    self.cfg[name][option] = value
            except:
                self.specto.logger.log(_("There was an reading the watches from %s") % self.file_name, "critical", self.__class__)

            try:
                f = open(self.file_name, "w")
                f.write(str(self.cfg).strip()) #write the new configuration file
            except IOError:
                self.specto.logger.log(_("There was an error writing to %s") % self.file_name, "critical", self.__class__)
            finally:
                f.close()
        

    def remove_watch(self, name):
        """ Remove a watch from the configuration file. """
        try:
            cfgpr = ConfigParser()
            cfgpr.read(self.file_name)
            cfgpr.remove_section(name)
            f = open(self.file_name, "w")
            cfgpr.write(open(self.file_name, "w"))
        except IOError:
            self.specto.logger.log(_("There was an error writing to %s") % self.file_name, "critical", self.__class__)
        finally:
            f.close()
        
    def is_unique_watch(self, name):
        """
        Returns True if the watch is found in the file.
        """
        try:
            self.cfg = ini_namespace(file(self.file_name))
            if not self.cfg._sections.has_key(name):
                return False
            else:
                return True
        except IOError:
            return False #this has to be an error
        
    def replace_name(self, name, new_name):
        """ Replace a watch name (rename). """
        #read the file
        try:
            f = open(self.file_name, "r")
            text = f.read()
        except IOError:
            self.specto.logger.log(_("There was an error writing to %s") % self.file_name, "critical", self.__class__)
        except:
            f.close
            
        text = text.replace("[" + name + "]", "[" + new_name + "]")
        
        if text:
            #replace and write file
            try:
                f = open(self.file_name, "w")
                f.write(text)
            except IOError:
                self.specto.logger.log(_("There was an error writing to %s") % self.file_name, "critical", self.__class__)
            finally:
                f.close()
