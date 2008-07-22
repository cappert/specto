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
import thread
import gtk

#specto imports
import spectlib.config
from spectlib.tools.iniparser import ini_namespace
from ConfigParser import ConfigParser
from spectlib import i18n
from spectlib.i18n import _

from time import sleep
from datetime import datetime
import base64 #encode/decode passwords

try:
    from spectlib.tools.keyringmanager import Keyring
    keyring = True
except:
    keyring = False

def gettext_noop(s):
   return s

class Watch:
    def __init__(self, specto, id, values, watch_values):
        self.specto = specto
        watch_values.extend([('name', spectlib.config.String(True)),
                            ('refresh', spectlib.config.Integer(True)),
                            ('type', spectlib.config.String(True)),
                            ('updated', spectlib.config.Boolean(False)),
                            ('command', spectlib.config.String(False)),
                            ('active', spectlib.config.Boolean(False)),
                            ('last_updated', spectlib.config.String(False)),
                            ('open_command', spectlib.config.String(False))
                            ])

        self.id = id
        self.use_network = False
        self.error = False
        self.actually_updated = False
        self.timer_id = -1
        self.deleted = False

        self.watch_values = watch_values
        self.set_values(values)
                
        self.watch_io = Watch_io(self.specto.FILE)
        
        global _
                    
    def start(self):
        """ Start the watch. """
        try:            
            self.active = True
            self.watch_io.write_option(self.name, 'active', self.active)
            self.start_update()
        except:
            self.error = True
            self.specto.logger.log(_("There was an error starting the watch"), "error", self.name)
            
    def stop(self):
        """ Stop the watch. """
        try:
            self.active = False
            self.watch_io.write_option(self.name, 'active', self.active)
            gobject.source_remove(self.timer_id)
        except:
            self.error = True
            self.specto.logger.log(_("There was an error stopping the watch"), "error", self.name)           

    def clear(self):
        """ clear the watch """
        try:
            self.updated = False
            self.watch_io.write_option(self.name, 'updated', self.updated)
            if not self.error:
                self.specto.mark_watch_status("idle-clear", self.id)
        except:
            self.error = True
            self.specto.logger.log(_("There was an error clearing the watch"), "error", self.name)

    def restart(self):
        """ restart the watch """
        if self.active == True:
            self.stop()
        self.start()        
        
    def start_update(self):
        try:
            if self.updated == True:
                self.specto.mark_watch_status("mark-updated", self.id)
            if self.use_network:
                if not self.check_connection():
                    return 
            self.specto.logger.log("Started update.", "debug", self.name)   
            self.specto.mark_watch_status("updating", self.id)
            self.error = False
            self.actually_updated = False
            #self.update()
            #return
            self.lock = thread.allocate_lock()
            self.lock.acquire()
            thread.start_new_thread(self.update,())
            while self.lock.locked():
                while gtk.events_pending():
                    gtk.main_iteration()
                time.sleep(0.05)
        except:
            self.error = True
            self.specto.logger.log(_("There was an error starting to update the watch"), "error", self.name)

                
                        
    def watch_updated(self):
        try:
            self.specto.logger.log("Watch is updated!", "info", self.name)   
            self.actually_updated = False
            self.updated = True            
            self.last_updated = datetime.today().strftime("%A %d %b %Y %H:%M")
            self.watch_io.write_option(self.name, 'updated', self.updated)
            self.watch_io.write_option(self.name, 'last_updated', self.last_updated)
            self.specto.mark_watch_status("updated", self.id)
            if self.command != "": #run watch specific updated commando
                os.system(self.command + " &")
        except:
            self.error = True
            self.specto.logger.log(_("There was an error marking the watch as updated"), "error", self.name)
                
        
    def timer_update(self):
        """ update the timer """
        try:
            if self.actually_updated == True:
                self.watch_updated()
            elif self.error == True:
                self.specto.mark_watch_status("error", self.id)
            elif self.active == False:
                self.stop()
            else:
                self.specto.mark_watch_status("idle", self.id)
            try:
                self.lock.release()
                self.timer_id = gobject.timeout_add(self.refresh, self.start_update)
            except:
                self.timer_id = gobject.timeout_add(self.refresh, self.update)
        except:
            self.error = True
            self.specto.logger.log(_("There was an error updating the watch"), "error", self.name)

    def check_connection(self):
        if  not self.specto.connection_manager.connected():
            self.specto.logger.log(_("No network connection detected"), "warning", self.name)
            self.specto.connection_manager.add_callback(self.start_update)
            self.specto.mark_watch_status("no-network", self.id)
            return False
        else :
            self.specto.mark_watch_status("network", self.id)
            #proxy support
            self.specto.specto_gconf.set_directory("/system/http_proxy")
            http_proxy = "http://%s:%s" % (self.specto.specto_gconf.get_entry("host"),
            self.specto.specto_gconf.get_entry("port")) 
            https_proxy = "https://%s:%s" % (self.specto.specto_gconf.get_entry("secure_host"),
            self.specto.specto_gconf.get_entry("secure_port")) 
            proxies = {"http": http_proxy, "https": https_proxy} 
            self.specto.specto_gconf.set_directory("")            
            return True
        
    def get_values(self):
        return self.values
        
    def set_values(self, values, validate=False):
        error_fields = ""
        for key, type in self.watch_values:
            try:
                value = values[key]
            except KeyError:
                if type.mandatory == False:
                    values[key] = type.getStandardValue()
                    value = values[key]
                    if not validate:
                        setattr(self, key, value)
                else:
                    error_fields += ", " + key
            else:    
                value = type.checkRestrictions(values[key])
                if value[0] == True:
                    if type.mandatory == True and value[1] == type.getStandardValue():
                        error_fields += ", " + key
                    else:
                        values[key] = value[1]
                        if not validate:
                            setattr(self, key, value[1])
                else:
                    error_fields += ", " + key
        
        if values['open_command'] == "":
            try:
                self.open_command = self.standard_open_command
            except:
                self.open_command = ""
            
        if self.last_updated == "":
            self.last_updated = "No updates yet"
                
        if len(error_fields) <> 0:
            error_fields = error_fields.lstrip(",")
            raise AttributeError, error_fields
        else:
            if not validate:
                self.values = values
        
    def get_balloon_text(self):        
        return "No message specified yet!"
    
    def get_extra_information(self):
        return "No extra information available."
    
    def remove_cache_files(self):
        return ""
        
class Watch_collection:
    def __init__(self, specto):
        self.watch_db = []
        self.id = 0
        self.plugin_dict = {}
        self.disabl_plugin_dict = {}
        self.specto = specto
        self.load_plugins()
                
    def load_plugins(self):
        dir = self.specto.SRC_PATH + "/plugins/"  
        for f in os.listdir(dir):
            if f[-3:] == ".py" and f != "__init__.py":
                if not os.path.exists('data'):
                    dir = "spectlib.plugins."
                else:
                    dir = "spectlib/plugins/"
                _file = dir + f[:-3]
                mod = __import__(_file, globals(), locals(), [''])
                obj = sys.modules[_file]

                self.plugin_dict[obj.type] = mod

                
    def create(self, values):
        """ read the content from the dictionary and create the watch """      
        _id = []
        for i in values:
            if values[i]['type'] == "0":
                values[i]['type'] = "Web_watch"
            if values[i]['type'] == "1":
                if values[i]['prot'] == "2":
                    values[i]['type'] = "Mail_watch_gmail"                    

            type = values[i]['type']
                        
            #get the right object and create the watch object
            mod = ""
            try:
                mod = self.plugin_dict[type]
            except:
                print "Please enable plugin \""+ type + "\", if you want to use the watch: "+ values[i]["name"] + "."
            
            if mod:  
                obj = getattr(mod, type)
                try:
                    watch_ = obj(self.specto, self.id, values[i])
                except AttributeError, error_fields:
                    if len(values) > 1:
                        pass
                    else:
                        raise AttributeError, error_fields
                else:
                    self.watch_db.append(watch_)
                    _id.append(self.id)
                    self.id+=1
                        
        return _id
        
    def remove(self, id):
        """ remove the watch from the collection """
        self.watch_db[id].stop()
        self.watch_db[id].updated = False   
        self.watch_db[id].deleted = True
        try:
            self.watch_db[id].remove_cache_files()
        except:
            pass
        self.specto.logger.remove_watch_log(self.watch_db[id].name)    
                
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
            if watch.active == True:
                watch.restart()
        
    def length(self):
        """ return the length from the collection """
        return len(self.watch_db)
    
    def count_updated_watches(self):
        """ Count the number of updated watches for the tooltip. """
        count_updates = {}
        for watch in self.watch_db:
            try:
                count_updates[watch.type_desc]
            except KeyError:
                count_updates[watch.type_desc] = 0
            
            if watch.updated == True:
                updates = count_updates[watch.type_desc]
                count_updates[watch.type_desc] = updates + 1
        
        return count_updates
    
    def find_watch(self, name):
        """
        Returns the key of a watch or None if it doesn't exists.
        """
        k = -1
        for watch in self.watch_db:
            if watch.name == name: 
                k = watch.id
                break
        return k
    
    def set_interval(self, refresh, refresh_unit):
        """
        Set the interval between the update checks.
        refresh = number
        refresh_unit = days, hours, minutes,... in values of 0, 1, 2, 3.
        """
        new_refresh = 0
        if refresh_unit == 0:#seconds
            new_refresh = refresh * 1000
        elif refresh_unit == 1:#minutes
            new_refresh = refresh * 60 * 1000
        elif refresh_unit == 2:#hours
            new_refresh = (refresh * 60) * 60 * 1000
        elif refresh_unit == 3:#days
            new_refresh = ((refresh * 60) * 60) * 24 *1000
        
        return new_refresh
        
    def get_interval(self, value):
        """ Get the interval between 2 updates. """
        if ((value / 60) / 60) / 24 / 1000 > 0:
            refresh_value = ((value / 60) / 60) / 24 / 1000
            type = 3
        elif (value / 60) / 60 / 1000 > 0:
            refresh_value = (value / 60) / 60 / 1000
            type = 2
        elif value / 60 / 1000 > 0:
            refresh_value = value / 60 / 1000
            type = 1
        else:
            refresh_value = value / 1000
            type = 0
            
        return refresh_value, type

        
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
        
        name = self.hide_brackets(name)    
        options = self.cfg._sections[name]._options.keys()
        
        for option_ in options:
            if option_ == "password" and not self.check_old_version(self.cfg[name]['type']): #don't use decoding for old watches.list
                option = self.read_option(name, option_)
                option = self.decode_password(name, option)
            else:
                option = self.read_option(name, option_)
                
            watch_options_ = { option_: option }
            watch_options.update(watch_options_)
        name = self.show_brackets(name)
        watch_options.update({'name':name})
                
        return watch_options
    
    def read_option(self, name, option):
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
            cfg = ini_namespace(file(self.file_name))
        except:
            return 0
        
        if cfg:
            name = self.hide_brackets(values['name'])
            if not cfg._sections.has_key(name):
                cfg.new_namespace(name) #add a new watch
                try:
                    f = open(self.file_name, "w")
                    f.write(str(cfg).strip()) #write the new configuration file
                except IOError:
                    self.specto.logger.log(_("There was an error writing to %s") % self.file_name, "critical", self.__class__)
                finally:
                    f.close()

            del values['name']
            for option, value  in values.iteritems():
                self.write_option(name, option, value)
                
            #except:
            #    self.specto.logger.log(_("There was an reading the watches from %s") % self.file_name, "critical", self.__class__)
                
    def write_option(self, name, option, value):
        try:
            cfg = ini_namespace(file(self.file_name))
        except:
            return 0
        
        if cfg:
            name = self.hide_brackets(name)
            if not cfg._sections.has_key(name):
                return 0
            else:
                if option == "password": # and self.check_old_version(self.cfg[name]['type']): #don't use encoding for old watches.list
                    value = self.encode_password(name, value)
                cfg[name][option] = value
                try:
                    f = open(self.file_name, "w")
                    f.write(str(cfg).strip()) #write the new configuration file
                except IOError:
                    self.specto.logger.log(_("There was an error writing to %s") % self.file_name, "critical", self.__class__)
                finally:
                    f.close()
        
        

    def remove_watch(self, name):
        """ Remove a watch from the configuration file. """
        try:
            cfgpr = ConfigParser()
            cfgpr.read(self.file_name)
            cfgpr.remove_section(self.hide_brackets(name))
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
            if not self.cfg._sections.has_key(self.hide_brackets(name)):
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
        
        name = self.hide_brackets(name)
        new_name = self.hide_brackets(new_name)
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
                
    def hide_brackets(self,name):
        name = name.replace("[", "&brStart;")
        name = name.replace("]", "&brEnd;")
        return name
        
    def show_brackets(self,name):
        name = name.replace("&brStart;", "[")
        name = name.replace("&brEnd;", "]")
        return name
    
    def encode_password(self, name, password):
        if keyring == True:
            k = Keyring(name, "Specto " + name, "network") 
            k.set_credentials((name, password))
            password = "**keyring**"
        else:
            password = base64.b64encode(password)
        return password
        
    def decode_password(self, name, password):
        if keyring == True:
            try:
                k = Keyring(name, "Specto " + name, "network")
                password = k.get_credentials()[1]
            except:
                try:
                    password = base64.b64decode(password)
                except TypeError:#password was not yet encoded
                    password = password
        else:
            try:
                password = base64.b64decode(password)
            except TypeError:#password was not yet encoded
                password = password
        return password
    
    def check_old_version(self, type):
        old = True
        try:
            int(type) #type is int: old version
            old = True
        except ValueError:
            old = False #type is not int: new version
        
        return old
            


