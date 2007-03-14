#!/usr/bin/env python
# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       add_watch.py
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

import sys, os
from spectlib.i18n import _
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


class Edit_watch:
    """
    Class to create the edit watch dialog.
    """
    #Please do not use confusing widget names such as 'lbl' and 'tbl', use full names like 'label' and 'table'.
    def __init__(self, specto, watch):
        self.watch = watch
        self.specto = specto
        #create tree
        gladefile= self.specto.PATH + 'glade/edit_watch.glade' 
        windowname= "edit_watch"
        self.wTree=gtk.glade.XML(gladefile,windowname, self.specto.glade_gettext)

        #catch some events
        dic= { "on_button_cancel_clicked": self.cancel_clicked,
        "on_button_save_clicked": self.save_clicked,
        "on_button_remove_clicked": self.remove_clicked,
        "on_button_clear_clicked": self.clear_clicked,#clear error_log textfield
        "on_button_save_as_clicked": self.save_as_clicked,#save error_log text
        "on_edit_watch_delete_event": self.delete_event,
        "on_refresh_unit_changed": self.set_refresh_values}

        #attach the events
        self.wTree.signal_autoconnect(dic)

        #set the info from the watch
        self.edit_watch=self.wTree.get_widget("edit_watch")
        self.edit_watch.set_title(_("Edit watch: ") + self.watch.name)
        self.wTree.get_widget("name").set_text(self.watch.name)
        icon = gtk.gdk.pixbuf_new_from_file(self.specto.PATH + 'icons/specto_window_icon.png' )
        self.edit_watch.set_icon(icon)
        self.edit_watch.set_resizable( False )

        refresh, refresh_unit = self.specto.get_interval(self.watch.refresh)
        self.wTree.get_widget("refresh_unit").set_active(refresh_unit)
        self.wTree.get_widget("refresh").set_value(refresh)
    
        #create the gui
        self.create_edit_gui()
        
        #put the logfile in the textview
        self.logwindow=gtk.TextBuffer(None)
        self.wTree.get_widget("error_log").set_buffer(self.logwindow)
        self.log = self.specto.logger.watch_log(self.watch.name)
        self.logwindow.set_text(self.log)
        
    def cancel_clicked(self,widget):
        """ Destroy the edit watch dialog. """
        self.edit_watch.destroy()
        
    def set_refresh_values(self, widget):
        """ Set the max and min values for the refresh unit. """
        digits = 0
        climb_rate = 1.0
        refresh_unit = self.wTree.get_widget("refresh_unit").get_active()
        
        if refresh_unit == 0 or refresh_unit == 1:
            adjustment = gtk.Adjustment(value=1, lower=1, upper=60, step_incr=1, page_incr=10, page_size=0)
        if refresh_unit == 2:
            adjustment = gtk.Adjustment(value=1, lower=1, upper=24, step_incr=1, page_incr=10, page_size=0)
        if refresh_unit == 3:
            adjustment = gtk.Adjustment(value=1, lower=1, upper=365, step_incr=1, page_incr=30, page_size=0)

        self.wTree.get_widget("refresh").configure(adjustment, climb_rate, digits)

    def save_clicked(self,widget):
        """ Save the new options from the edited watch. """
        values = {}
        #get the standard options from a watch
        values['name'] = self.wTree.get_widget("name").get_text()#FIXME: cfgparse cannot have single quotes (') it seems. We must watch out for the watch name or arguments not to have them.
        if self.specto.check_unique_watch(values['name']):
            self.specto.replace_name(self.watch.name, values['name'])
            #change the name in the array
            self.specto.watch_db[self.watch.id].set_name(values['name'])
            #change the name in the notifier window
            self.specto.notifier.change_name(values['name'], self.watch.id)
            
        values['type'] = self.watch.type
        values['refresh_value'] = self.wTree.get_widget("refresh").get_value_as_int()
        values['refresh_unit'] =  self.wTree.get_widget("refresh_unit").get_active()
        
        self.specto.watch_db[self.watch.id].set_refresh(self.specto.set_interval(values['refresh_value'], values['refresh_unit']))
        
        #get the watch dependant options
        if values['type'] == 0: #add a website
            values['url'] = self.txtUrl.get_text()
            values['error_margin'] = (self.adjustment.get_value() / 100)
            
            self.specto.watch_db[self.watch.id].set_url(values['url'])
            self.specto.watch_db[self.watch.id].set_error_margin(values['error_margin'])

        elif values['type'] == 1: #add an email
            prot = self.watch.prot
            
            values.update(
            {'username': self.txtUsername.get_text(),
            'password': self.txtPassword.get_text(),
            'prot': prot}
            )
            
            self.specto.watch_db[self.watch.id].set_username(values['username'])
            self.specto.watch_db[self.watch.id].set_password(values['password'])
            
            if int(values['prot']) != 2: #gmail doesn't need a host
                values.update({'host': self.txtHost.get_text(), 'ssl': self.chkSsl.get_active() })
                self.specto.watch_db[self.watch.id].set_host(values['host'])
                self.specto.watch_db[self.watch.id].set_ssl(values['ssl'])
                
        elif values['type'] == 2: #add a file
            values['file'] = self.btnFile.get_filename()
            self.specto.watch_db[self.watch.id].set_file(values['file'])
            
        elif values['type'] == 3: #add a process
            values['process'] = self.txtProcess.get_text()
            self.specto.watch_db[self.watch.id].set_process(values['process'])

        elif values['type'] == 4: #add a port
            values['port'] = self.txtPort.get_text()
            self.specto.watch_db[self.watch.id].set_port(values['port'])
            
        self.edit_watch.destroy()
        
        if self.watch.active == True:
            self.specto.stop_watch(self.watch.id)
            
        self.specto.edit_watch(values)#write the options in the configuration file
        
        self.specto.start_watch(self.watch.id)
        
        if self.watch.active == False:
            self.specto.stop_watch(self.watch.id)
        self.specto.logger.log(_("Watch : \"%s\" edited.") % values['name'], "info", self.__class__)
        #"del self" would be useful here I think.

    def remove_clicked(self,widget):
        """ Remove the watch. """
        name = self.wTree.get_widget("name").get_text()
        self.edit_watch.destroy()
        self.specto.remove_watch(name, self.watch.id) #remove the watch

    def clear_clicked(self,widget):
        """ Clear the log window. """
        self.specto.logger.remove_watch_log(self.watch.name)
        self.specto.logger.log(_("removed logs from watch: \"%s\"") % self.watch.name, "info", self.__class__)
        self.log = self.specto.logger.watch_log(self.watch.name)
        self.logwindow.set_text(self.log)
        
    def save_as_clicked(self,widget):
        """ Open the Save as dialog window. """
        Save_dialog(self, self.log)

    def delete_event(self, widget, event, data=None):
        """ Destroy the window. """
        self.edit_watch.destroy()
        return True

    def create_edit_gui(self):
        """ Create the gui for the different kinds of watches. """
        vbox_options = self.wTree.get_widget("vbox_edit_options")

        if self.watch.type == 0:
            ###create the web options gui
            tblWeb = gtk.Table(rows=2, columns=2, homogeneous=False)
            tblWeb.set_row_spacings(6)
            tblWeb.set_col_spacings(6)
            tblWeb.show()

            #url
            labelUrl = gtk.Label(_("URL:"))
            labelUrl.set_alignment(xalign=0.0, yalign=0.5)
            labelUrl.show()
            tblWeb.attach(labelUrl, 0, 1, 0, 1)

            self.txtUrl = gtk.Entry()
            self.txtUrl.set_text(self.watch.url_)
            self.txtUrl.show()
            tblWeb.attach(self.txtUrl, 1, 2, 0, 1)

            #error margin
            labelSlider = gtk.Label(_("Error Margin (%):"))
            labelSlider.set_alignment(xalign=0.0, yalign=0.5)
            labelSlider.show()
            tblWeb.attach(labelSlider, 0, 1, 2, 3)

            self.adjustment = gtk.Adjustment(value=2.0, lower=0, upper=50, step_incr=0.1, page_incr=1.0, page_size=10)
            self.margin_scale = gtk.HScale(adjustment=self.adjustment)
            self.margin_scale.set_digits(1)
            self.margin_scale.set_value_pos(gtk.POS_RIGHT)
            self.margin_scale.show()
            margin = float(self.watch.error_margin) * 100
            self.margin_scale.set_value(margin)
            self.margin_scale.show()
            tblWeb.attach(self.margin_scale, 0, 2, 3, 4)

            vbox_options.pack_start(tblWeb, False, False, 0)

        elif self.watch.type == 1:
            ###create the mail options gui
            tblMail = gtk.Table(rows=4, columns=2, homogeneous=False)
            tblMail.set_row_spacings(6)
            tblMail.set_col_spacings(6)

            tblMail.show()

            #protocol
            labelProtocol = gtk.Label(_("Protocol:"))
            labelProtocol.set_alignment(xalign=0.0, yalign=0.5)
            labelProtocol.show()
            tblMail.attach(labelProtocol, 0, 1, 0, 1)
            
            self.labelProtocol_text = gtk.Label()
            self.labelProtocol_text.set_alignment(0.0,0.0)
            self.labelProtocol_text.show()
            tblMail.attach(self.labelProtocol_text, 1 ,2, 0, 1)                

            #username
            labelUsername = gtk.Label(_("Username:"))
            labelUsername.set_alignment(xalign=0.0, yalign=0.5)
            labelUsername.show()
            tblMail.attach(labelUsername, 0, 1, 1, 2)

            self.txtUsername = gtk.Entry()
            self.txtUsername.set_text(self.watch.user)
            self.txtUsername.show()
            tblMail.attach(self.txtUsername, 1, 2, 1, 2)

            #password
            labelPassword = gtk.Label(_("Password:"))
            labelPassword.set_alignment(xalign=0.0, yalign=0.5)
            labelPassword.show()
            tblMail.attach(labelPassword, 0, 1, 2, 3)

            self.txtPassword = gtk.Entry()
            self.txtPassword.set_text(self.watch.password)
            self.txtPassword.set_visibility(False)
            self.txtPassword.show()
            tblMail.attach(self.txtPassword, 1, 2, 2, 3)

            #host
            labelHost = gtk.Label(_("Host:"))
            labelHost.set_alignment(xalign=0.0, yalign=0.5)
            tblMail.attach(labelHost, 0, 1, 3, 4)

            self.txtHost = gtk.Entry()
            tblMail.attach(self.txtHost, 1, 2, 3, 4)
            
            #ssl
            labelSsl = gtk.Label(_("Use SSL:"))
            labelSsl.set_alignment(xalign=0.0, yalign=0.5)
            tblMail.attach(labelSsl, 0, 1, 4, 5)
            
            self.chkSsl = gtk.CheckButton(None, True)
            tblMail.attach(self.chkSsl, 1, 2, 4, 5)  

            if self.watch.prot == 0:
                self.labelProtocol_text.set_text(_("Pop3"))
                labelHost.show()
                self.txtHost.set_text(self.watch.host)
                self.txtHost.show()
                labelSsl.show()
                self.chkSsl.show()
                if str(self.watch.ssl) == 'True':
                    self.chkSsl.set_active(True)
                else:
                    self.chkSsl.set_active(False)
                
            elif self.watch.prot == 1:
                self.labelProtocol_text.set_text(_("Imap"))
                labelHost.show()
                self.txtHost.set_text(self.watch.host)
                self.txtHost.show()
                labelSsl.show()
                self.chkSsl.show()
                if str(self.watch.ssl) == 'True':
                    self.chkSsl.set_active(True)
                else:
                    self.chkSsl.set_active(False) 
                                                  
            else:
                self.labelProtocol_text.set_text(_("Gmail"))

            vbox_options.pack_start(tblMail, False, False, 0)
            
        elif self.watch.type == 2:
            ###create the file options gui
            tblFile = gtk.Table(rows=2, columns=2, homogeneous=False)
            tblFile.set_row_spacings(6)
            tblFile.set_col_spacings(6)
            tblFile.show()
            
            #file/folder
            self.labelFile = gtk.Label(_("File/folder:"))
            self.labelFile.set_alignment(xalign=0.0, yalign=0.5)
            self.labelFile.show()
            tblFile.attach(self.labelFile, 0, 1, 0, 1)
    
            #option file/folder
            vbox_file = gtk.HBox(False, 10)
            vbox_file.show()
            tblFile.attach(vbox_file, 1, 2, 0, 1)
    
            self.chkFile = gtk.RadioButton(None, _("File"))
            self.chkFile.connect("toggled", self.change_file_type)
            vbox_file.pack_start(self.chkFile, True, True, 0)
            self.chkFile.show()
    
            self.chkFolder = gtk.RadioButton(self.chkFile, _("Folder"))
            self.chkFolder.connect("toggled", self.change_file_type)
            vbox_file.pack_start(self.chkFolder, True, True, 0)
            self.chkFolder.show()
    
            #file selection
            self.btnFile = gtk.FileChooserButton(_("Choose a file or folder"))
            self.btnFile.set_filename(self.watch.file)
            self.btnFile.show()
            tblFile.attach(self.btnFile, 0, 2, 1, 2)
            
            if self.watch.mode == "folder":
                self.chkFolder.set_active(True)
            else:
                self.chkFile.set_active(True)
            self.btnFile.set_filename(self.watch.file)

            vbox_options.pack_start(tblFile, False, False, 0)
        
        elif self.watch.type == 3: #add a process
            tblProcess = gtk.Table(rows=2, columns=1, homogeneous=False)
            tblProcess.set_row_spacings(6)
            tblProcess.set_col_spacings(6)
            tblProcess.show()
            
            labelProcess = gtk.Label(_("Process:"))
            labelProcess.set_alignment(xalign=0.0, yalign=0.5)
            labelProcess.show()
            tblProcess.attach(labelProcess, 0, 1, 0, 1)
            
            self.txtProcess = gtk.Entry()
            self.txtProcess.set_text(self.watch.process)
            self.txtProcess.show()
            tblProcess.attach(self.txtProcess, 1, 2, 0, 1)
            
            vbox_options.pack_start(tblProcess, False, False, 0)

        elif self.watch.type == 4: #add a port
            tblPort = gtk.Table(rows=2, columns=1, homogeneous=False)
            tblPort.set_row_spacings(6)
            tblPort.set_col_spacings(6)
            tblPort.show()
            
            labelPort = gtk.Label(_("Port:"))
            labelPort.set_alignment(xalign=0.0, yalign=0.5)
            labelPort.show()
            tblPort.attach(labelPort, 0, 1, 0, 1)
            
            self.txtPort = gtk.Entry()
            self.txtPort.set_text(self.watch.port)
            self.txtPort.show()
            tblPort.attach(self.txtPort, 1, 2, 0, 1)
            
            vbox_options.pack_start(tblPort, False, False, 0)

    
    def change_file_type(self, *args):
        """ Change the file chooser action (folder/file) for a file watch. """
        if self.chkFolder.get_active() == True:
            self.btnFile.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        else:
            self.btnFile.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
           

class Save_dialog:
    """
    Class to create the save dialog.
    """
    
    def __init__(self, specto, *args):
        """ Display the save as dialog. """
        self.specto = specto
        self.text = args[0]
        #create tree
        gladefile= self.specto.PATH + 'glade/edit_watch.glade' 
        windowname= "file_chooser"
        self.wTree=gtk.glade.XML(gladefile,windowname)        
        self.save_dialog = self.wTree.get_widget("file_chooser")
        
        dic={
        "on_button_cancel_clicked": self.cancel,
        "on_button_save_clicked": self.save
        }
        #attach the events
        self.wTree.signal_autoconnect(dic)        
            
        icon = gtk.gdk.pixbuf_new_from_file(self.specto.PATH + 'icons/specto_window_icon.png' )
        self.save_dialog.set_icon(icon)
        self.save_dialog.set_filename(os.environ['HOME'] + "/ ")
        
    def cancel(self, *args):
        """ Destroy the window. """
        self.save_dialog.destroy()
        
    def save(self, *args):
        """ Save the file. """
        file_name = self.save_dialog.get_filename()
        
        f = open(file_name, "w")
        f.write(self.text)
        f.close()  
        
        self.save_dialog.destroy()

if __name__ == "__main__":
    #run the gui
    app=edit_watch()
    gtk.main()
