#!/usr/bin/env python
# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       logger.py
#
# Copyright (c) 2005-2007, Jean-François Fortin Tam
# This module code is maintained by : Jean-François Fortin and Wout Clymans

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
import logging
import sys, os
import re
from specto.i18n import _

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

try:
    import gtk
    import gtk.glade
except:
    pass
        
class Log_dialog:
    """ 
    Class to create the log dialog window. 
    """
    
    def __init__(self, specto):
        self.specto = specto
        #create tree
        gladefile= self.specto.PATH + 'glade/log_dialog.glade'
        windowname= "log_dialog"
        self.wTree=gtk.glade.XML(gladefile,windowname)
        
        dic={
        "on_button_help_clicked": self.show_help,
        "on_button_save_clicked": self.save,
        "on_button_clear_clicked": self.clear,
        "on_button_close_clicked": self.delete_event,
        "on_button_find_clicked": self.find
        }
        #attach the events
        self.wTree.signal_autoconnect(dic)
        
        self.log_dialog=self.wTree.get_widget("log_dialog")
        icon = gtk.gdk.pixbuf_new_from_file(self.specto.PATH + 'icons/specto_window_icon.png' )
        self.log_dialog.set_icon(icon)
        
        self.wTree.get_widget("combo_level").set_active(0)
        
        #read the log file
        self.read_log() 
        
        self.logwindow=gtk.TextBuffer(None)
        self.wTree.get_widget("log_field").set_buffer(self.logwindow) 
        self.logwindow.set_text(self.log)
        
    def save(self, widget):
        """ Save the text in the logwindow. """
        text = self.logwindow.get_text(self.logwindow.get_start_iter(), self.logwindow.get_end_iter())     
        self.save = Save_dialog(self, text)
        
    def clear(self, widget):
        """ Clear the text in the log window and from the log file. """
        self.logwindow.set_text("")
        f = open(self.file_name, "w")
        f.write("")
        f.close()
        os.chmod(self.file_name, 0600)
        
    def find(self, widget):
        """ Find the lines in the log file that contain the filter word. """
        level = self.wTree.get_widget("combo_level").get_active()
        buffer_log = self.log.split("\n")
        filtered_log = ""

        if level == 0:
            self.logwindow.set_text(self.log)
        else:
            if level == 1:
                pattern = _("\w\s*- DEBUG -\s*\w")
            elif level == 2:
                pattern = _("\w\s*- INFO -\s*\w")
            elif level == 3:
                pattern = _("\w\s*- WARNING -\s*\w")
            elif level == 4:
                pattern = _("\w\s*- ERROR -\s*\w")
            elif level == 5:
                pattern = _("\w\s*- CRITICAL -\s*\w")
            elif level == -1:
                pattern = self.wTree.get_widget("combo_level").child.get_text()
                
            for i in buffer_log:
                if re.search(pattern, i):
                    filtered_log += i + "\n"
                    
            self.logwindow.set_text(filtered_log)
    
    def read_log(self):
        """ Read the log file. """
        self.file_name = os.environ['HOME'] + "/.specto/" + "specto.log"
        if not os.path.exists(self.file_name):
            f = open(self.file_name, "w")
            f.close()
        os.chmod(self.file_name, 0600)
        
        log_file = open(self.file_name, "r")
        self.log = log_file.read()
        log_file.close()
           
    def show_help(self, widget):
        """ Show the help webpage. """
        self.specto.util.show_webpage("http://specto.ecchi.ca/Manual/Troubleshooting")
        
    def delete_event(self, widget, *args):
        """ Close the window. """
        self.log_dialog.destroy()
        return True
        
        
class Save_dialog:
    """ 
    Class for displaying the save as dialog.
    """
        
    def __init__(self, specto, *args):
        self.specto = specto
        #create tree
        gladefile= self.specto.PATH + 'glade/log_dialog.glade' 
        windowname= "file_chooser"
        self.wTree=gtk.glade.XML(gladefile,windowname)        
        self.save_dialog = self.wTree.get_widget("file_chooser")
        
        dic={
        "on_button_cancel_clicked": self.cancel,
        "on_button_save_clicked": self.save
        }
        #attach the events
        self.wTree.signal_autoconnect(dic)
            
        icon = gtk.gdk.pixbuf_new_from_file(self.specto.PATH + 'icons/specto_window_icon.png')
        self.save_dialog.set_icon(icon)
        self.save_dialog.set_filename(os.environ['HOME'] + "/ ")
        
        self.text = args[0]
        
    def cancel(self, *args):
        """ Close the save as dialog. """
        self.save_dialog.destroy()
        
    def save(self, *args):
        """ Save the file. """
        file_name = self.save_dialog.get_filename()

        if not os.path.exists(file_name):
            f = open(file_name, "w")
            f.close()
        os.chmod(file_name, 0600)
                        
        f = open(file_name, "w")
        f.write(self.text)
        f.close()  
        
        self.save_dialog.destroy()
       
    

class Logger:
    """
    Class for logging in Specto.
    """

    def __init__(self, specto):
        self.specto = specto
        self.file_name = os.environ['HOME'] + "/.specto/" + "specto.log"

        if not os.path.exists(self.file_name):
            f = open(self.file_name, "a")
            f.close()
        os.chmod(self.file_name, 0600)
        
        #write to log file
        #TODO:XXX: Do we need to gettextize it? Maybe just the date.
        logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)-12s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename=self.file_name,
                    filemode='a')
        
        #write to console
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(levelname)s - %(name)-12s - %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)            

    def log(self, message, level, logger):
        """ Log a message. """
        log = logging.getLogger(str(logger)[7:])
        
        if self.specto.DEBUG == True:
            if level == "debug":
                log.debug(message)
            elif level == "info":
                log.info(message)
            elif level == "warning":
                log.warn(message)
            elif level == "error":
                log.error(message)
            else:
                log.critical(message)
                
    def read_log(self):
        """ Read the log file. """
        #get the info from the log file
        log_file = open(self.file_name, "r")
        self.logfile = log_file.read()
        log_file.close()
                
    def watch_log(self, watch_name):
        """ Filter the log for a watch name. """
        self.read_log()
        buffer_log = self.logfile.split("\n")
        filtered_log = ""
        
        for i in buffer_log:
            if re.search(watch_name, i):
                filtered_log += i + "\n"
                
        return filtered_log
    
    def remove_watch_log(self, watch_name):
        """ Remove a watch from the log file. """
        self.read_log()
        buffer_log = self.logfile.split("\n")
        filtered_log = ""
        
        for i in buffer_log:
            if not re.search(watch_name, i):
                filtered_log += i + "\n"
                
        f = open(self.file_name, "w")
        f.write(filtered_log)
        f.close()
        
    def clear_log(self, *args):
        """ Clear the log file. """
        f = open(self.file_name, "w")
        f.write("")
        f.close()
        os.chmod(self.file_name, 0600)
